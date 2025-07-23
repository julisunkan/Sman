from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import User, SocialMediaAccount, Purchase, Transaction, FooterPage, SupportMessage, SystemSettings, db
from forms import AdminAccountVerificationForm, AdminPaymentVerificationForm, AdminDepositVerificationForm, AdminUserManagementForm, FooterPageForm, SystemSettingsForm, TestEmailForm, AdminSupportResponseForm
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
        user.verification_token = None  # Clear verification token
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
            ('routing_number', form.routing_number.data, 'Bank routing number', 'bank'),
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
    form.routing_number.data = current_settings.get('routing_number', '')
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
