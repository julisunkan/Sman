from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
from forms import LoginForm, RegisterForm, ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from utils import send_email_notification

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.password_hash and check_password_hash(user.password_hash, form.password.data or ''):
            if not user.active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)
            
            # Check if user needs to change password
            if hasattr(user, 'force_password_change') and user.force_password_change:
                login_user(user, remember=form.remember_me.data)
                flash('You must change your password before continuing.', 'warning')
                return redirect(url_for('auth.change_password'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            
            if user.role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()
        
        if existing_username:
            flash('Username already exists. Please choose a different username.', 'danger')
            return render_template('auth/register.html', form=form)
        
        if existing_email:
            flash('Email address already registered. Please use a different email or try logging in.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Check if referral code is valid
        referrer = None
        if form.referral_code.data:
            referrer = User.query.filter_by(referral_code=form.referral_code.data).first()
            if not referrer:
                flash('Invalid referral code.', 'warning')
                return render_template('auth/register.html', form=form)
        
        try:
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data or ''),
                referred_by_id=referrer.id if referrer else None
            )
            
            db.session.add(user)
            db.session.commit()
            
            # Generate and send verification token
            token = user.generate_verification_token()
            db.session.commit()
            
            # Send verification email with beautiful template
            verification_url = url_for('auth.verify_email', token=token, _external=True)
            
            # Get referral rate for welcome email
            from models import SystemSettings
            referral_setting = SystemSettings.query.filter_by(setting_key='referral_rate').first()
            referral_rate = f"{referral_setting.setting_value}%" if referral_setting and referral_setting.setting_value else "5%"
            
            try:
                send_email_notification(
                    user.email, 
                    'Welcome to SocialMarket - Verify Your Account',
                    f'Please click this link to verify your account: {verification_url}',
                    template_name='welcome.html',
                    template_data={
                        'user_name': user.username,
                        'verification_url': verification_url,
                        'referral_code': user.referral_code,
                        'referral_rate': referral_rate
                    }
                )
            except Exception as e:
                # Registration still successful even if email fails
                print(f"Email sending failed: {e}")
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html', form=form)
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user or user.email_verification_expires < datetime.utcnow():
        flash('Invalid or expired verification token.', 'danger')
        return redirect(url_for('auth.login'))
    
    user.is_verified = True
    user.email_verification_token = None
    user.email_verification_expires = None
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/resend-verification')
@login_required
def resend_verification():
    if current_user.is_verified:
        flash('Your email is already verified.', 'info')
        return redirect(url_for('main.dashboard'))
    
    token = current_user.generate_verification_token()
    db.session.commit()
    
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    send_email_notification(
        current_user.email,
        'Verify Your Account',
        f'Please click this link to verify your account: {verification_url}'
    )
    
    flash('Verification email sent! Please check your email.', 'success')
    return redirect(url_for('main.dashboard'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Update password
        current_user.password_hash = generate_password_hash(form.new_password.data or '')
        current_user.force_password_change = False
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Generate password reset token
            token = user.generate_password_reset_token()
            db.session.commit()
            
            # Send password reset email with beautiful template
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_email_notification(
                user.email,
                'Password Reset Request - Secure Your Account',
                f'Click this link to reset your password: {reset_url}',
                template_name='password_reset.html',
                template_data={
                    'user_name': user.username,
                    'reset_url': reset_url
                }
            )
        
        # Always show the same message for security
        flash('If an account with that email exists, we\'ve sent you a password reset link.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.verify_password_reset_token(token):
        flash('Invalid or expired password reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Update password and clear reset token
        user.password_hash = generate_password_hash(form.password.data or '')
        user.password_reset_token = None
        user.password_reset_expires = None
        user.force_password_change = False
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form)
