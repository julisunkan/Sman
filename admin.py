from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from models import User, SocialMediaAccount, Purchase, Transaction, FooterPage, SupportMessage, SystemSettings, db
from forms import AdminAccountVerificationForm, AdminPaymentVerificationForm, AdminUserManagementForm, FooterPageForm
from utils import send_email_notification, calculate_referral_commission
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'verified_users': User.query.filter_by(is_verified=True).count(),
        'total_accounts': SocialMediaAccount.query.count(),
        'pending_accounts': SocialMediaAccount.query.filter_by(status='pending').count(),
        'approved_accounts': SocialMediaAccount.query.filter_by(status='approved').count(),
        'total_purchases': Purchase.query.count(),
        'pending_purchases': Purchase.query.filter_by(status='pending').count(),
        'completed_purchases': Purchase.query.filter_by(status='completed').count(),
        'pending_deposits': Transaction.query.filter_by(transaction_type='deposit', status='pending').count(),
        'total_revenue': db.session.query(func.sum(Purchase.amount)).filter_by(status='completed').scalar() or 0,
        'open_support_tickets': SupportMessage.query.filter_by(status='open').count()
    }
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_accounts = SocialMediaAccount.query.order_by(SocialMediaAccount.created_at.desc()).limit(5).all()
    recent_purchases = Purchase.query.order_by(Purchase.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_users=recent_users,
                         recent_accounts=recent_accounts,
                         recent_purchases=recent_purchases)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminUserManagementForm(obj=user)
    
    if form.validate_on_submit():
        user.is_active = form.is_active.data
        user.kyc_status = form.kyc_status.data
        db.session.commit()
        
        # Send notification to user
        status_message = 'activated' if user.is_active else 'deactivated'
        send_email_notification(
            user.email,
            'Account Status Update',
            f'Your account has been {status_message}.'
        )
        
        flash(f'User {user.username} updated successfully.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/manage_user.html', user=user, form=form)

@admin_bp.route('/accounts')
@login_required
@admin_required
def accounts():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = SocialMediaAccount.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    accounts = query.order_by(SocialMediaAccount.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/accounts.html', accounts=accounts, status_filter=status_filter)

@admin_bp.route('/accounts/<int:account_id>/verify', methods=['GET', 'POST'])
@login_required
@admin_required
def verify_account(account_id):
    account = SocialMediaAccount.query.get_or_404(account_id)
    form = AdminAccountVerificationForm()
    
    if form.validate_on_submit():
        account.status = form.status.data
        account.is_verified = (form.status.data == 'approved')
        account.verification_notes = form.verification_notes.data
        db.session.commit()
        
        # Notify seller
        status_message = 'approved and is now available for sale' if account.is_verified else 'rejected'
        send_email_notification(
            account.seller.email,
            'Account Verification Update',
            f'Your {account.platform} account (@{account.username}) has been {status_message}.'
        )
        
        flash(f'Account verification updated.', 'success')
        return redirect(url_for('admin.accounts'))
    
    return render_template('admin/verify_account.html', account=account, form=form)

@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    page = request.args.get('page', 1, type=int)
    payment_type = request.args.get('type', 'purchases')  # purchases or deposits
    
    if payment_type == 'deposits':
        transactions = Transaction.query.filter_by(transaction_type='deposit').order_by(
            Transaction.created_at.desc()
        ).paginate(page=page, per_page=20, error_out=False)
        return render_template('admin/payments.html', transactions=transactions, payment_type=payment_type)
    else:
        purchases = Purchase.query.order_by(Purchase.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        return render_template('admin/payments.html', purchases=purchases, payment_type=payment_type)

@admin_bp.route('/payments/purchase/<int:purchase_id>/verify', methods=['GET', 'POST'])
@login_required
@admin_required
def verify_purchase_payment(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    form = AdminPaymentVerificationForm()
    
    if form.validate_on_submit():
        purchase.status = form.status.data
        purchase.verified_by_admin = True
        purchase.admin_notes = form.admin_notes.data
        
        if form.status.data == 'completed':
            # Release account details
            purchase.details_released = True
            purchase.completed_at = datetime.utcnow()
            
            # Update account status
            purchase.account.status = 'sold'
            
            # Process referral commission if buyer was referred
            buyer = purchase.buyer
            if buyer.referred_by_id:
                commission = calculate_referral_commission(purchase.amount)
                referrer = User.query.get(buyer.referred_by_id)
                referrer.balance += commission
                referrer.total_referral_earnings += commission
                
                # Create transaction record
                referral_transaction = Transaction(
                    user_id=referrer.id,
                    transaction_type='referral_earning',
                    amount=commission,
                    description=f'Referral commission from {buyer.username} purchase',
                    status='completed'
                )
                db.session.add(referral_transaction)
            
            # Notify buyer
            send_email_notification(
                purchase.buyer.email,
                'Purchase Approved - Account Details Available',
                f'Your purchase of {purchase.account.platform} account has been approved. Login details are now available in your dashboard.'
            )
            
            # Notify seller
            send_email_notification(
                purchase.account.seller.email,
                'Account Sold Successfully',
                f'Your {purchase.account.platform} account has been sold for ${purchase.amount}.'
            )
        
        db.session.commit()
        flash('Payment verification updated.', 'success')
        return redirect(url_for('admin.payments'))
    
    return render_template('admin/verify_payment.html', purchase=purchase, form=form)

@admin_bp.route('/payments/deposit/<int:transaction_id>/verify', methods=['GET', 'POST'])
@login_required
@admin_required
def verify_deposit(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    form = AdminPaymentVerificationForm()
    
    if form.validate_on_submit():
        transaction.status = form.status.data
        transaction.admin_verified = True
        
        if form.status.data == 'completed':
            # Add funds to user's wallet
            transaction.user.balance += transaction.amount
            
            # Notify user
            send_email_notification(
                transaction.user.email,
                'Deposit Approved',
                f'Your deposit of ${transaction.amount} has been approved and added to your wallet.'
            )
        
        db.session.commit()
        flash('Deposit verification updated.', 'success')
        return redirect(url_for('admin.payments'))
    
    return render_template('admin/verify_deposit.html', transaction=transaction, form=form)

@admin_bp.route('/footer-pages')
@login_required
@admin_required
def footer_pages():
    pages = FooterPage.query.all()
    return render_template('admin/footer_pages.html', pages=pages)

@admin_bp.route('/footer-pages/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_footer_page():
    form = FooterPageForm()
    
    if form.validate_on_submit():
        page = FooterPage(
            title=form.title.data,
            slug=form.slug.data,
            content=form.content.data,
            is_active=form.is_active.data
        )
        db.session.add(page)
        db.session.commit()
        
        flash('Footer page created successfully.', 'success')
        return redirect(url_for('admin.footer_pages'))
    
    return render_template('admin/edit_footer_page.html', form=form, page=None)

@admin_bp.route('/footer-pages/<int:page_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_footer_page(page_id):
    page = FooterPage.query.get_or_404(page_id)
    form = FooterPageForm(obj=page)
    
    if form.validate_on_submit():
        page.title = form.title.data
        page.slug = form.slug.data
        page.content = form.content.data
        page.is_active = form.is_active.data
        db.session.commit()
        
        flash('Footer page updated successfully.', 'success')
        return redirect(url_for('admin.footer_pages'))
    
    return render_template('admin/edit_footer_page.html', form=form, page=page)

@admin_bp.route('/footer-pages/<int:page_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_footer_page(page_id):
    page = FooterPage.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    
    flash('Footer page deleted successfully.', 'success')
    return redirect(url_for('admin.footer_pages'))

@admin_bp.route('/support')
@login_required
@admin_required
def support_messages():
    page = request.args.get('page', 1, type=int)
    messages = SupportMessage.query.order_by(SupportMessage.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/support_messages.html', messages=messages)

@admin_bp.route('/support/<int:message_id>/respond', methods=['POST'])
@login_required
@admin_required
def respond_to_support(message_id):
    message = SupportMessage.query.get_or_404(message_id)
    response = request.form.get('response')
    
    if response:
        message.admin_response = response
        message.status = 'closed'
        db.session.commit()
        
        # Send email to user
        send_email_notification(
            message.user.email,
            f'Response to: {message.subject}',
            response
        )
        
        flash('Response sent successfully.', 'success')
    
    return redirect(url_for('admin.support_messages'))
