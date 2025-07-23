from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import User, SocialMediaAccount, Purchase, Transaction, FooterPage, SupportMessage, SystemSettings, Withdrawal, db
from forms import AdminAccountVerificationForm, AdminPaymentVerificationForm, AdminDepositVerificationForm, AdminUserManagementForm, AdminCreateUserForm, FooterPageForm, SystemSettingsForm, AdminWithdrawalForm, TestEmailForm, AdminSupportResponseForm, AdminEditAccountForm, SettingsImportForm, SettingsExportForm
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

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Redirect admin root to dashboard"""
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(active=True).count(),
        'verified_users': User.query.filter_by(is_verified=True).count(),
        'pending_kyc': User.query.filter_by(kyc_status='pending').count(),
        'total_accounts': SocialMediaAccount.query.count(),
        'pending_accounts': SocialMediaAccount.query.filter_by(status='pending').count(),
        'approved_accounts': SocialMediaAccount.query.filter_by(status='approved').count(),
        'total_purchases': Purchase.query.count(),
        'pending_purchases': Purchase.query.filter_by(status='pending').count(),
        'completed_purchases': Purchase.query.filter_by(status='completed').count(),
        'pending_deposits': Transaction.query.filter_by(transaction_type='deposit', status='pending').count(),
        'pending_withdrawals': Withdrawal.query.filter_by(status='pending').count(),
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

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = AdminCreateUserForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        
        if existing_user:
            if existing_user.username == form.username.data:
                flash('Username already exists. Please choose a different one.', 'danger')
            else:
                flash('Email already exists. Please use a different email.', 'danger')
            return render_template('admin/create_user.html', form=form)
        
        # Create new user
        from werkzeug.security import generate_password_hash
        password_data = form.password.data or ""
        user = User(  # type: ignore
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            password_hash=generate_password_hash(password_data),
            role=form.role.data,
            is_verified=form.is_verified.data,
            active=form.active.data,
            balance=form.balance.data or 0,
            kyc_status=form.kyc_status.data,
            created_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email if verified
        if form.is_verified.data:
            try:
                send_email_notification(
                    to_email=user.email,
                    subject='Welcome to SocialMarket - Account Created',
                    body=f'Your account has been created by an administrator. Username: {user.username}',
                    template_name='welcome',
                    template_data={'user': user}
                )
            except Exception as e:
                flash(f'User created but welcome email failed: {str(e)}', 'warning')
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html', form=form)

@admin_bp.route('/users/<int:user_id>/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminUserManagementForm(obj=user)
    
    if form.validate_on_submit():
        user.active = form.active.data
        user.kyc_status = form.kyc_status.data
        db.session.commit()
        
        # Send notification to user
        status_message = 'activated' if user.active else 'deactivated'
        send_email_notification(
            user.email,
            'Account Status Update',
            f'Your account has been {status_message}.'
        )
        
        flash(f'User {user.username} updated successfully.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/manage_user.html', user=user, form=form)

@admin_bp.route('/kyc-reviews')
@login_required
@admin_required
def kyc_reviews():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'pending')
    
    # Filter users based on KYC status
    query = User.query.filter(User.kyc_document_path.isnot(None))
    if status_filter and status_filter != 'all':
        query = query.filter_by(kyc_status=status_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/kyc_reviews.html', users=users, status_filter=status_filter)

@admin_bp.route('/kyc-reviews/<int:user_id>/verify', methods=['GET', 'POST'])
@login_required
@admin_required
def verify_kyc(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        notes = request.form.get('notes', '')
        
        if action == 'approve':
            user.kyc_status = 'verified'
            message = 'KYC document approved successfully.'
            email_subject = 'KYC Verification Approved'
            email_body = f'Your KYC document has been verified. You can now create account listings.'
        elif action == 'reject':
            user.kyc_status = 'rejected'
            message = 'KYC document rejected.'
            email_subject = 'KYC Verification Rejected'
            email_body = f'Your KYC document has been rejected. Reason: {notes}. Please submit a new document.'
        else:
            flash('Invalid action.', 'danger')
            return redirect(url_for('admin.kyc_reviews'))
        
        db.session.commit()
        
        # Send notification to user
        send_email_notification(user.email, email_subject, email_body)
        
        flash(message, 'success')
        return redirect(url_for('admin.kyc_reviews'))
    
    return render_template('admin/verify_kyc.html', user=user)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot modify admin user status.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.active = not user.active
    db.session.commit()
    
    status_message = 'activated' if user.active else 'deactivated'
    send_email_notification(
        user.email,
        'Account Status Update',
        f'Your account has been {status_message} by an administrator.'
    )
    
    flash(f'User {user.username} {status_message} successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/verify-email', methods=['POST'])
@login_required
@admin_required
def verify_user_email(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.is_verified:
        flash(f'User {user.username} is already verified.', 'info')
    else:
        user.is_verified = True
        user.email_verification_token = None  # Clear verification token
        db.session.commit()
        
        send_email_notification(
            user.email,
            'Email Verified',
            'Your email address has been manually verified by an administrator. You now have full access to your account.'
        )
        
        flash(f'User {user.username} email verified successfully.', 'success')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    
    # Set flag to force password change on next login
    user.force_password_change = True
    db.session.commit()
    
    flash(f'Password reset for {user.username}. User will be forced to change password on next login.', 'success')
    return redirect(url_for('admin.users'))

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
        
        # Notify seller with beautiful email template
        if account.is_verified:
            send_email_notification(
                account.seller.email,
                'Account Listing Approved!',
                f'Your account listing has been approved.',
                template_name='account_approved.html',
                template_data={
                    'seller_name': account.seller.username,
                    'account_username': account.username,
                    'account_platform': account.platform,
                    'account_followers': account.followers_count,
                    'account_price': account.price,
                    'account_category': account.category,
                    'admin_notes': form.verification_notes.data,
                    'account_url': url_for('main.account_detail', account_id=account.id, _external=True)
                }
            )
        else:
            send_email_notification(
                account.seller.email,
                'Account Listing Update Required',
                f'Your account listing needs some changes.',
                template_name='account_rejected.html',
                template_data={
                    'seller_name': account.seller.username,
                    'account_username': account.username,
                    'account_platform': account.platform,
                    'account_followers': account.followers_count,
                    'admin_notes': form.verification_notes.data,
                    'account_edit_url': url_for('main.edit_listing', account_id=account.id, _external=True)
                }
            )
        
        flash(f'Account verification updated.', 'success')
        return redirect(url_for('admin.accounts'))
    
    return render_template('admin/verify_account.html', account=account, form=form)

@admin_bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_account(account_id):
    account = SocialMediaAccount.query.get_or_404(account_id)
    form = AdminEditAccountForm(obj=account)
    
    if form.validate_on_submit():
        # Update account details
        account.platform = form.platform.data
        account.username = form.username.data
        account.followers_count = form.followers_count.data
        account.engagement_rate = form.engagement_rate.data
        account.price = form.price.data
        account.description = form.description.data
        account.category = form.category.data
        account.account_url = form.account_url.data
        account.login_email = form.login_email.data
        account.login_password = form.login_password.data
        account.status = form.status.data
        account.verification_notes = form.verification_notes.data
        account.is_verified = (form.status.data == 'approved')
        account.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Notify seller of changes with beautiful template
        if account.is_verified:
            send_email_notification(
                account.seller.email,
                'Account Listing Updated and Approved',
                f'Your account listing has been updated and approved.',
                template_name='account_approved.html',
                template_data={
                    'seller_name': account.seller.username,
                    'account_username': account.username,
                    'account_platform': account.platform,
                    'account_followers': account.followers_count,
                    'account_price': account.price,
                    'account_category': account.category,
                    'admin_notes': form.verification_notes.data or 'Listing updated by administrator.',
                    'account_url': url_for('main.account_detail', account_id=account.id, _external=True)
                }
            )
        else:
            send_email_notification(
                account.seller.email,
                'Account Listing Updated',
                f'Your account listing has been updated.',
                template_name='account_rejected.html',
                template_data={
                    'seller_name': account.seller.username,
                    'account_username': account.username,
                    'account_platform': account.platform,
                    'account_followers': account.followers_count,
                    'admin_notes': form.verification_notes.data or 'Listing updated by administrator.',
                    'account_edit_url': url_for('main.edit_listing', account_id=account.id, _external=True)
                }
            )
        
        flash(f'Account listing updated successfully.', 'success')
        return redirect(url_for('admin.accounts'))
    
    return render_template('admin/edit_account.html', account=account, form=form)

@admin_bp.route('/accounts/<int:account_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_account(account_id):
    account = SocialMediaAccount.query.get_or_404(account_id)
    
    # Check if account has any active purchases
    active_purchases = Purchase.query.filter_by(account_id=account_id, status='pending').count()
    if active_purchases > 0:
        flash('Cannot delete account with pending purchases. Please complete or cancel them first.', 'danger')
        return redirect(url_for('admin.accounts'))
    
    # Store seller info for notification
    seller_email = account.seller.email
    account_info = f'{account.platform} account (@{account.username})'
    
    # Delete the account
    db.session.delete(account)
    db.session.commit()
    
    # Notify seller
    send_email_notification(
        seller_email,
        'Account Listing Deleted',
        f'Your {account_info} listing has been removed by an administrator.'
    )
    
    flash(f'Account listing deleted successfully.', 'success')
    return redirect(url_for('admin.accounts'))

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
                if referrer:
                    referrer.balance += commission
                    referrer.total_referral_earnings += commission
                
                    # Create transaction record
                    referral_transaction = Transaction(  # type: ignore
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

@admin_bp.route('/withdrawals')
@login_required
@admin_required
def withdrawals():
    """Admin view for managing withdrawal requests"""
    page = request.args.get('page', 1, type=int)
    withdrawals = Withdrawal.query.order_by(Withdrawal.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/withdrawals.html', withdrawals=withdrawals)

@admin_bp.route('/withdrawals/<int:withdrawal_id>/process', methods=['GET', 'POST'])
@login_required
@admin_required
def process_withdrawal(withdrawal_id):
    """Process withdrawal request"""
    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)
    form = AdminWithdrawalForm()
    
    if form.validate_on_submit():
        withdrawal.status = form.status.data
        withdrawal.admin_notes = form.admin_notes.data
        withdrawal.processed_by_admin_id = current_user.id
        withdrawal.processed_at = datetime.utcnow()
        
        # Update corresponding transaction
        withdrawal_transaction = Transaction.query.filter_by(
            user_id=withdrawal.user_id,
            transaction_type='withdrawal',
            amount=-withdrawal.amount,
            status='pending'
        ).first()
        
        if form.status.data == 'approved':
            # Withdrawal approved - funds already deducted
            if withdrawal_transaction:
                withdrawal_transaction.status = 'completed'
            
            # Notify user
            send_email_notification(
                withdrawal.user.email,
                'Withdrawal Approved',
                f'Your withdrawal request of ₦{withdrawal.amount:,.2f} has been approved. Payment will be processed within 2-3 business days.',
                template_data={
                    'user_name': withdrawal.user.username,
                    'amount': withdrawal.amount,
                    'bank_name': withdrawal.bank_name,
                    'account_number': withdrawal.account_number,
                    'account_name': withdrawal.account_name
                }
            )
            
        elif form.status.data == 'rejected':
            # Withdrawal rejected - refund the amount
            withdrawal.user.balance += withdrawal.amount
            if withdrawal_transaction:
                withdrawal_transaction.status = 'rejected'
            
            # Create refund transaction
            refund_transaction = Transaction(  # type: ignore
                user_id=withdrawal.user_id,
                transaction_type='refund',
                amount=withdrawal.amount,
                description=f'Withdrawal refund - ₦{withdrawal.amount}',
                status='completed'
            )
            db.session.add(refund_transaction)
            
            # Notify user
            send_email_notification(
                withdrawal.user.email,
                'Withdrawal Rejected',
                f'Your withdrawal request of ₦{withdrawal.amount:,.2f} has been rejected. The amount has been refunded to your wallet.',
                template_data={
                    'user_name': withdrawal.user.username,
                    'amount': withdrawal.amount,
                    'reason': form.admin_notes.data or 'No reason provided'
                }
            )
            
        elif form.status.data == 'paid':
            # Mark as paid - final status
            if withdrawal_transaction:
                withdrawal_transaction.status = 'completed'
            
            # Notify user
            send_email_notification(
                withdrawal.user.email,
                'Withdrawal Completed',
                f'Your withdrawal of ₦{withdrawal.amount:,.2f} has been successfully processed and sent to your bank account.',
                template_data={
                    'user_name': withdrawal.user.username,
                    'amount': withdrawal.amount,
                    'bank_name': withdrawal.bank_name
                }
            )
        
        db.session.commit()
        flash(f'Withdrawal request {form.status.data}.', 'success')
        return redirect(url_for('admin.withdrawals'))
    
    return render_template('admin/process_withdrawal.html', withdrawal=withdrawal, form=form)

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
        try:
            # Check if slug already exists
            existing_page = FooterPage.query.filter_by(slug=form.slug.data).first()
            if existing_page:
                flash('A page with this URL slug already exists. Please choose a different slug.', 'danger')
                return render_template('admin/edit_footer_page.html', form=form, page=None)
            
            page = FooterPage(  # type: ignore
                title=form.title.data or '',
                slug=form.slug.data or '',
                content=form.content.data or '',
                is_active=form.is_active.data if form.is_active.data is not None else True
            )
            db.session.add(page)
            db.session.commit()
            
            flash('Footer page created successfully.', 'success')
            return redirect(url_for('admin.footer_pages'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating footer page: {str(e)}', 'danger')
    else:
        # Display form validation errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
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

@admin_bp.route('/support-messages')
@login_required
@admin_required
def support_messages():
    page = request.args.get('page', 1, type=int)
    messages = SupportMessage.query.order_by(SupportMessage.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    form = AdminSupportResponseForm()
    return render_template('admin/support_messages.html', messages=messages, form=form)

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    form = SystemSettingsForm()
    
    if form.validate_on_submit():
        # Save all settings
        settings_to_save = [
            ('bank_name', form.bank_name.data, 'Bank name for deposits', 'bank'),
            ('account_number', form.account_number.data, 'Bank account number', 'bank'),
            ('account_name', form.account_name.data, 'Bank account holder name', 'bank'),
            ('smtp_server', form.smtp_server.data, 'SMTP server hostname', 'smtp'),
            ('smtp_port', str(form.smtp_port.data) if form.smtp_port.data else '', 'SMTP server port', 'smtp'),
            ('smtp_username', form.smtp_username.data, 'SMTP username', 'smtp'),
            ('smtp_password', form.smtp_password.data, 'SMTP password', 'smtp'),
            ('smtp_use_tls', str(form.smtp_use_tls.data), 'Use TLS for SMTP', 'smtp'),
            ('from_email', form.from_email.data, 'Default from email address', 'smtp'),
            ('from_name', form.from_name.data, 'Default from name', 'smtp'),
            ('site_name', form.site_name.data, 'Website name', 'general'),
            ('site_description', form.site_description.data, 'Website description', 'general'),
            ('commission_rate', str(form.commission_rate.data) if form.commission_rate.data else '', 'Platform commission rate (%)', 'general'),
            ('referral_rate', str(form.referral_rate.data) if form.referral_rate.data else '', 'Referral commission rate (%)', 'general'),
            ('min_deposit', str(form.min_deposit.data) if form.min_deposit.data else '', 'Minimum deposit amount', 'general'),
            ('max_file_size', str(form.max_file_size.data) if form.max_file_size.data else '', 'Maximum file size (MB)', 'general'),
            ('facebook_url', form.facebook_url.data, 'Facebook page URL', 'social'),
            ('twitter_url', form.twitter_url.data, 'Twitter profile URL', 'social'),
            ('instagram_url', form.instagram_url.data, 'Instagram profile URL', 'social'),
            ('telegram_url', form.telegram_url.data, 'Telegram channel URL', 'social'),
            ('linkedin_url', form.linkedin_url.data, 'LinkedIn profile URL', 'social'),
            ('youtube_url', form.youtube_url.data, 'YouTube channel URL', 'social'),
        ]
        
        for key, value, description, category in settings_to_save:
            if value is not None and value != '':
                setting = SystemSettings.query.filter_by(setting_key=key).first()
                if setting:
                    setting.setting_value = value
                    setting.updated_at = func.now()
                else:
                    setting = SystemSettings(  # type: ignore
                        setting_key=key,
                        setting_value=value,
                        description=description,
                        category=category
                    )
                    db.session.add(setting)
        
        db.session.commit()
        flash('System settings updated successfully!', 'success')
        return redirect(url_for('admin.system_settings'))
    
    # Load current settings
    settings = SystemSettings.query.all()
    current_settings = {s.setting_key: s.setting_value for s in settings}
    
    # Populate form with current values
    form.bank_name.data = current_settings.get('bank_name', '')
    form.account_number.data = current_settings.get('account_number', '')
    form.account_name.data = current_settings.get('account_name', '')
    form.smtp_server.data = current_settings.get('smtp_server', '')
    form.smtp_port.data = int(current_settings.get('smtp_port', 587)) if current_settings.get('smtp_port') else 587
    form.smtp_username.data = current_settings.get('smtp_username', '')
    form.smtp_password.data = current_settings.get('smtp_password', '')
    form.smtp_use_tls.data = current_settings.get('smtp_use_tls', 'True') == 'True'
    form.from_email.data = current_settings.get('from_email', '')
    form.from_name.data = current_settings.get('from_name', 'SocialMarket')
    form.site_name.data = current_settings.get('site_name', 'SocialMarket')
    form.site_description.data = current_settings.get('site_description', '')
    form.commission_rate.data = float(current_settings.get('commission_rate', 5.0)) if current_settings.get('commission_rate') else 5.0
    form.referral_rate.data = float(current_settings.get('referral_rate', 5.0)) if current_settings.get('referral_rate') else 5.0
    form.min_deposit.data = float(current_settings.get('min_deposit', 1000.0)) if current_settings.get('min_deposit') else 1000.0
    form.max_file_size.data = int(current_settings.get('max_file_size', 10)) if current_settings.get('max_file_size') else 10
    form.facebook_url.data = current_settings.get('facebook_url', '')
    form.twitter_url.data = current_settings.get('twitter_url', '')
    form.instagram_url.data = current_settings.get('instagram_url', '')
    form.telegram_url.data = current_settings.get('telegram_url', '')
    form.linkedin_url.data = current_settings.get('linkedin_url', '')
    form.youtube_url.data = current_settings.get('youtube_url', '')
    
    return render_template('admin/system_settings.html', form=form, current_settings=current_settings)

@admin_bp.route('/test-email', methods=['GET', 'POST'])
@login_required
@admin_required
def test_email():
    form = TestEmailForm()
    
    if form.validate_on_submit():
        try:
            # Get SMTP settings
            settings = SystemSettings.query.all()
            smtp_settings = {s.setting_key: s.setting_value for s in settings}
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_settings.get('from_email', 'noreply@socialmarket.com')
            msg['To'] = form.test_email.data
            msg['Subject'] = form.subject.data
            
            msg.attach(MIMEText(form.message.data or '', 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_settings.get('smtp_server', 'localhost'), 
                                int(smtp_settings.get('smtp_port', 587)))
            if smtp_settings.get('smtp_use_tls', 'True') == 'True':
                server.starttls()
            
            smtp_username = smtp_settings.get('smtp_username')
            smtp_password = smtp_settings.get('smtp_password')
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            flash(f'Test email sent successfully to {form.test_email.data}!', 'success')
        except Exception as e:
            flash(f'Failed to send test email: {str(e)}', 'danger')
        
        return redirect(url_for('admin.test_email'))
    
    return render_template('admin/test_email.html', form=form)

# Email Template Management Routes
@admin_bp.route('/email-templates')
@login_required
@admin_required
def email_templates():
    """Display email template management page"""
    return render_template('admin/email_templates.html')

@admin_bp.route('/email-templates/preview/<template>')
@login_required
@admin_required
def preview_email_template(template):
    """Preview an email template with sample data"""
    from flask import render_template
    
    # Sample data for different templates
    sample_data = {
        'welcome': {
            'user_name': 'John Doe',
            'verification_url': url_for('auth.verify_email', token='sample-token', _external=True),
            'referral_code': 'SAMPLE123',
            'referral_rate': '5%'
        },
        'password_reset': {
            'user_name': 'John Doe',
            'reset_url': url_for('auth.reset_password', token='sample-token', _external=True)
        },
        'purchase_confirmation': {
            'buyer_name': 'John Doe',
            'account_username': 'sample_account',
            'account_platform': 'instagram',
            'account_followers': 10000,
            'purchase_amount': 50000.0,
            'account_email': 'account@example.com',
            'account_password': 'sample_password',
            'account_url': 'https://instagram.com/sample_account',
            'platform_commission': 2500.0,
            'seller_payment': 47500.0,
            'referral_commission': 1250.0,
            'purchase_id': 'PUR123',
            'dashboard_url': url_for('main.dashboard', _external=True)
        },
        'sale_notification': {
            'seller_name': 'Jane Doe',
            'account_username': 'sample_account',
            'account_platform': 'instagram',
            'account_followers': 10000,
            'sale_amount': 50000.0,
            'seller_earnings': 47500.0,
            'platform_fee': 2500.0,
            'commission_rate': '5%',
            'buyer_name': 'John Doe',
            'new_balance': 75000.0,
            'sale_date': datetime.now().strftime('%B %d, %Y'),
            'transaction_id': 'TXN123',
            'dashboard_url': url_for('main.dashboard', _external=True)
        },
        'account_approved': {
            'seller_name': 'Jane Doe',
            'account_username': 'sample_account',
            'account_platform': 'instagram',
            'account_followers': 10000,
            'account_price': 50000.0,
            'account_category': 'lifestyle',
            'admin_notes': 'Account verified successfully. Good engagement rate and authentic followers.',
            'account_url': url_for('main.account_detail', account_id=1, _external=True)
        },
        'account_rejected': {
            'seller_name': 'Jane Doe',
            'account_username': 'sample_account',
            'account_platform': 'instagram',
            'account_followers': 10000,
            'admin_notes': 'Please provide clearer screenshots and verify follower authenticity.',
            'account_edit_url': url_for('main.edit_listing', account_id=1, _external=True)
        }
    }
    
    if template not in sample_data:
        flash('Template not found.', 'danger')
        return redirect(url_for('admin.email_templates'))
    
    try:
        # Get site settings for template
        site_settings = SystemSettings.query.filter(
            SystemSettings.setting_key.in_(['site_name', 'site_description'])
        ).all()
        
        template_context = {
            'subject': f'Sample {template.replace("_", " ").title()} Email',
            'site_name': next((s.setting_value for s in site_settings if s.setting_key == 'site_name'), 'SocialMarket'),
            'site_description': next((s.setting_value for s in site_settings if s.setting_key == 'site_description'), 'Your trusted social media marketplace'),
            **sample_data[template]
        }
        
        # Render the template
        html_content = render_template(f'emails/{template}.html', **template_context)
        return html_content
        
    except Exception as e:
        flash(f'Error previewing template: {str(e)}', 'danger')
        return redirect(url_for('admin.email_templates'))

@admin_bp.route('/email-templates/test/<template>')
@login_required
@admin_required  
def test_email_template(template):
    """Send a test email using the specified template"""
    try:
        # Send test email to admin
        sample_data = {
            'user_name': current_user.username,
            'verification_url': url_for('auth.verify_email', token='test-token', _external=True),
            'reset_url': url_for('auth.reset_password', token='test-token', _external=True),
            'referral_code': 'TEST123',
            'referral_rate': '5%'
        }
        
        send_email_notification(
            current_user.email,
            f'Test Email - {template.replace("_", " ").title()}',
            f'This is a test email for the {template} template.',
            template_name=f'{template}.html',
            template_data=sample_data
        )
        
        flash(f'Test email sent successfully to {current_user.email}', 'success')
        
    except Exception as e:
        flash(f'Error sending test email: {str(e)}', 'danger')
        
    return redirect(url_for('admin.email_templates'))

@admin_bp.route('/support-messages/<int:message_id>/respond', methods=['POST'])
@login_required
@admin_required
def respond_to_support(message_id):
    message = SupportMessage.query.get_or_404(message_id)
    form = AdminSupportResponseForm()
    
    if form.validate_on_submit():
        try:
            message.admin_response = form.response.data
            message.status = 'closed'
            db.session.commit()
            
            # Send email to user
            try:
                send_email_notification(
                    message.user.email,
                    f'Response to: {message.subject}',
                    form.response.data or ''
                )
                flash('Response sent successfully and user notified by email.', 'success')
            except Exception as e:
                flash(f'Response saved but email notification failed: {str(e)}', 'warning')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving response: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.support_messages'))

@admin_bp.route('/settings/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_settings():
    """Import system settings from JSON file"""
    form = SettingsImportForm()
    
    if form.validate_on_submit():
        import json
        import tempfile
        import os
        
        try:
            
            # Save uploaded file temporarily
            uploaded_file = form.settings_file.data
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
                uploaded_file.save(temp_file.name)
                
                # Read and parse JSON
                with open(temp_file.name, 'r') as f:
                    settings_data = json.load(f)
                
                # Clean up temp file
                os.unlink(temp_file.name)
            
            # Validate JSON structure
            if not isinstance(settings_data, dict):
                flash('Invalid settings file format. Expected JSON object.', 'danger')
                return render_template('admin/import_settings.html', form=form)
            
            # Import settings
            imported_count = 0
            skipped_count = 0
            
            for key, value in settings_data.items():
                existing_setting = SystemSettings.query.filter_by(setting_key=key).first()
                
                if existing_setting and not form.overwrite_existing.data:
                    skipped_count += 1
                    continue
                
                if existing_setting:
                    existing_setting.setting_value = str(value)
                else:
                    new_setting = SystemSettings()  # type: ignore
                    new_setting.setting_key = key
                    new_setting.setting_value = str(value)
                    db.session.add(new_setting)
                
                imported_count += 1
            
            db.session.commit()
            
            flash(f'Settings imported successfully! {imported_count} settings imported, {skipped_count} skipped.', 'success')
            return redirect(url_for('admin.system_settings'))
            
        except json.JSONDecodeError:
            flash('Invalid JSON file format.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error importing settings: {str(e)}', 'danger')
    
    return render_template('admin/import_settings.html', form=form)

@admin_bp.route('/settings/export', methods=['GET', 'POST'])
@login_required
@admin_required
def export_settings():
    """Export system settings to JSON file"""
    form = SettingsExportForm()
    
    if form.validate_on_submit():
        try:
            import json
            from flask import make_response
            
            # Get settings based on export type
            export_type = form.export_type.data
            
            if export_type == 'all':
                settings = SystemSettings.query.all()
            elif export_type == 'bank':
                bank_keys = ['bank_name', 'account_number', 'account_name']
                settings = SystemSettings.query.filter(SystemSettings.setting_key.in_(bank_keys)).all()
            elif export_type == 'smtp':
                smtp_keys = ['smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_tls', 'from_email', 'from_name']
                settings = SystemSettings.query.filter(SystemSettings.setting_key.in_(smtp_keys)).all()
            elif export_type == 'general':
                general_keys = ['site_name', 'site_description', 'commission_rate', 'referral_rate', 'min_deposit', 'max_file_size']
                settings = SystemSettings.query.filter(SystemSettings.setting_key.in_(general_keys)).all()
            elif export_type == 'social':
                social_keys = ['facebook_url', 'twitter_url', 'instagram_url', 'telegram_url', 'linkedin_url', 'youtube_url']
                settings = SystemSettings.query.filter(SystemSettings.setting_key.in_(social_keys)).all()
            else:
                settings = []
            
            # Convert to dictionary
            settings_dict = {s.setting_key: s.setting_value for s in settings}
            
            # Create JSON response
            json_data = json.dumps(settings_dict, indent=2)
            
            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=socialmarket_settings_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            flash(f'Settings exported successfully! {len(settings_dict)} settings exported.', 'success')
            return response
            
        except Exception as e:
            flash(f'Error exporting settings: {str(e)}', 'danger')
    
    return render_template('admin/export_settings.html', form=form)
