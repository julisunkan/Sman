from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from models import User, SocialMediaAccount, Purchase, Transaction, FooterPage, SupportMessage, db
from forms import ProfileForm, KYCForm, SocialMediaAccountForm, DepositForm, PurchaseForm, SupportMessageForm, SearchForm
from utils import save_file, format_currency, format_number, send_email_notification
from sqlalchemy import or_, and_, func
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get featured accounts (approved and available)
    featured_accounts = SocialMediaAccount.query.filter_by(
        status='approved'
    ).order_by(SocialMediaAccount.followers_count.desc()).limit(8).all()
    
    # Get platform statistics
    platform_stats = {}
    platforms = ['instagram', 'tiktok', 'youtube', 'twitter', 'facebook']
    for platform in platforms:
        count = SocialMediaAccount.query.filter_by(
            platform=platform, status='approved'
        ).count()
        platform_stats[platform] = count
    
    return render_template('index.html', 
                         featured_accounts=featured_accounts,
                         platform_stats=platform_stats,
                         format_currency=format_currency,
                         format_number=format_number)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_verified:
        flash('Please verify your email address to access all features.', 'warning')
    
    # User's statistics
    user_accounts = SocialMediaAccount.query.filter_by(seller_id=current_user.id).all()
    user_purchases = Purchase.query.filter_by(buyer_id=current_user.id).all()
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(
        Transaction.created_at.desc()
    ).limit(5).all()
    
    # Referral statistics
    referred_users = User.query.filter_by(referred_by_id=current_user.id).all()
    
    stats = {
        'total_accounts': len(user_accounts),
        'active_listings': len([a for a in user_accounts if a.status == 'approved']),
        'total_purchases': len(user_purchases),
        'wallet_balance': current_user.balance,
        'total_referrals': len(referred_users),
        'referral_earnings': current_user.total_referral_earnings
    }
    
    return render_template('profile/profile.html', 
                         stats=stats,
                         recent_transactions=user_transactions,
                         format_currency=format_currency)

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.phone = form.phone.data
        current_user.country = form.country.data
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('profile/edit_profile.html', form=form)

@main_bp.route('/profile/kyc', methods=['GET', 'POST'])
@login_required
def kyc_verification():
    form = KYCForm()
    
    if form.validate_on_submit():
        if current_user.kyc_status == 'verified':
            flash('Your KYC is already verified.', 'info')
            return redirect(url_for('main.dashboard'))
        
        document_path = save_file(form.document.data, 'kyc_documents')
        if document_path:
            current_user.kyc_document_path = document_path
            current_user.kyc_status = 'pending'
            db.session.commit()
            
            flash('KYC document uploaded successfully. Verification is pending.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Failed to upload document. Please ensure file is under 15KB.', 'danger')
    
    return render_template('profile/kyc.html', form=form)

@main_bp.route('/wallet')
@login_required
def wallet():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(
        Transaction.created_at.desc()
    ).all()
    
    return render_template('wallet/wallet.html', 
                         transactions=transactions,
                         format_currency=format_currency)

@main_bp.route('/wallet/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    form = DepositForm()
    
    # Get bank details from system settings
    from models import SystemSettings
    settings = SystemSettings.query.all()
    bank_settings = {s.setting_key: s.setting_value for s in settings}
    
    # Get minimum deposit amount for validation
    min_deposit_setting = SystemSettings.query.filter_by(setting_key='min_deposit').first()
    min_deposit = float(min_deposit_setting.setting_value) if min_deposit_setting and min_deposit_setting.setting_value else 1.0
    
    if form.validate_on_submit():
        # Validate minimum deposit amount
        if form.amount.data and form.amount.data < min_deposit:
            flash(f'Minimum deposit amount is {format_currency(min_deposit)}', 'danger')
            return render_template('wallet/deposit.html', form=form, bank_settings=bank_settings, format_currency=format_currency)
        payment_proof_path = save_file(form.payment_proof.data, 'payment_proofs')
        if payment_proof_path:
            transaction = Transaction(  # type: ignore
                user_id=current_user.id,
                transaction_type='deposit',
                amount=form.amount.data,
                description=f'Wallet deposit - ₦{form.amount.data}',
                payment_proof_path=payment_proof_path,
                status='pending'
            )
            db.session.add(transaction)
            db.session.commit()
            
            flash('Deposit request submitted successfully. Admin verification pending.', 'success')
            return redirect(url_for('main.wallet'))
        else:
            flash('Failed to upload payment proof. Please ensure file is under 15KB.', 'danger')
    
    return render_template('wallet/deposit.html', form=form, bank_settings=bank_settings, format_currency=format_currency)

@main_bp.route('/accounts')
def browse_accounts():
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = SocialMediaAccount.query.filter_by(status='approved')
    
    # Apply filters
    if request.args.get('platform'):
        query = query.filter_by(platform=request.args.get('platform'))
    
    if request.args.get('category'):
        query = query.filter_by(category=request.args.get('category'))
    
    if request.args.get('min_price'):
        try:
            min_price_str = request.args.get('min_price')
            if min_price_str:
                min_price = float(min_price_str)
                query = query.filter(SocialMediaAccount.price >= min_price)
        except (ValueError, TypeError):
            pass
    
    if request.args.get('max_price'):
        try:
            max_price_str = request.args.get('max_price')
            if max_price_str:
                max_price = float(max_price_str)
                query = query.filter(SocialMediaAccount.price <= max_price)
        except (ValueError, TypeError):
            pass
    
    if request.args.get('min_followers'):
        try:
            min_followers_str = request.args.get('min_followers')
            if min_followers_str:
                min_followers = int(min_followers_str)
                query = query.filter(SocialMediaAccount.followers_count >= min_followers)
        except (ValueError, TypeError):
            pass
    
    # Sort by price or followers
    sort_by = request.args.get('sort', 'newest')
    if sort_by == 'price_low':
        query = query.order_by(SocialMediaAccount.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(SocialMediaAccount.price.desc())
    elif sort_by == 'followers':
        query = query.order_by(SocialMediaAccount.followers_count.desc())
    else:
        query = query.order_by(SocialMediaAccount.created_at.desc())
    
    accounts = query.paginate(page=page, per_page=12, error_out=False)
    
    return render_template('accounts/browse.html', 
                         accounts=accounts,
                         form=form,
                         format_currency=format_currency,
                         format_number=format_number)

@main_bp.route('/accounts/<int:account_id>')
def account_detail(account_id):
    account = SocialMediaAccount.query.get_or_404(account_id)
    
    if account.status != 'approved':
        flash('Account not available.', 'warning')
        return redirect(url_for('main.browse_accounts'))
    
    # Check if current user is the seller
    is_seller = current_user.is_authenticated and current_user.id == account.seller_id
    
    return render_template('accounts/account_detail.html', 
                         account=account,
                         is_seller=is_seller,
                         format_currency=format_currency,
                         format_number=format_number)

@main_bp.route('/accounts/<int:account_id>/purchase', methods=['GET', 'POST'])
@login_required
def purchase_account(account_id):
    account = SocialMediaAccount.query.get_or_404(account_id)
    
    if account.status != 'approved':
        flash('Account not available for purchase.', 'danger')
        return redirect(url_for('main.browse_accounts'))
    
    if account.seller_id == current_user.id:
        flash('You cannot purchase your own account.', 'danger')
        return redirect(url_for('main.account_detail', account_id=account_id))
    
    # Check if user has already purchased this account
    existing_purchase = Purchase.query.filter_by(
        buyer_id=current_user.id,
        account_id=account_id
    ).first()
    
    if existing_purchase:
        flash('You have already purchased this account.', 'info')
        return redirect(url_for('main.transaction_history'))
    
    form = PurchaseForm()
    form.account_id.data = account_id
    
    if form.validate_on_submit():
        payment_proof_path = save_file(form.payment_proof.data, 'payment_proofs')
        if payment_proof_path:
            purchase = Purchase(  # type: ignore
                buyer_id=current_user.id,
                account_id=account_id,
                amount=account.price,
                payment_proof_path=payment_proof_path,
                status='pending'
            )
            db.session.add(purchase)
            db.session.commit()
            
            # Notify seller
            send_email_notification(
                account.seller.email,
                'New Purchase Request',
                f'Someone wants to purchase your {account.platform} account (@{account.username}) for ₦{account.price}.'
            )
            
            flash('Purchase request submitted successfully. Admin verification pending.', 'success')
            return redirect(url_for('main.transaction_history'))
        else:
            flash('Failed to upload payment proof. Please ensure file is under 15KB.', 'danger')
    
    return render_template('accounts/purchase.html', account=account, form=form, format_currency=format_currency)

@main_bp.route('/accounts/create', methods=['GET', 'POST'])
@login_required
def create_listing():
    if not current_user.is_verified:
        flash('Please verify your email before creating listings.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if current_user.kyc_status != 'verified':
        flash('Please complete KYC verification before creating listings.', 'warning')
        return redirect(url_for('main.kyc_verification'))
    
    form = SocialMediaAccountForm()
    
    if form.validate_on_submit():
        screenshot_path = save_file(form.screenshot.data, 'screenshots')
        if screenshot_path:
            account = SocialMediaAccount(  # type: ignore
                platform=form.platform.data,
                username=form.username.data,
                followers_count=form.followers_count.data,
                engagement_rate=form.engagement_rate.data,
                price=form.price.data,
                description=form.description.data,
                category=form.category.data,
                login_email=form.login_email.data,
                login_password=form.login_password.data,
                screenshot_path=screenshot_path,
                seller_id=current_user.id,
                status='pending'
            )
            db.session.add(account)
            db.session.commit()
            
            flash('Account listing created successfully. Admin verification pending.', 'success')
            return redirect(url_for('main.my_listings'))
        else:
            flash('Failed to upload screenshot. Please ensure file is under 15KB.', 'danger')
    
    return render_template('accounts/create_listing.html', form=form)

@main_bp.route('/my-listings')
@login_required
def my_listings():
    accounts = SocialMediaAccount.query.filter_by(seller_id=current_user.id).order_by(
        SocialMediaAccount.created_at.desc()
    ).all()
    
    return render_template('accounts/my_listings.html', 
                         accounts=accounts,
                         format_currency=format_currency,
                         format_number=format_number)

@main_bp.route('/transactions')
@login_required
def transaction_history():
    page = request.args.get('page', 1, type=int)
    
    # Get user's purchases
    purchases = Purchase.query.filter_by(buyer_id=current_user.id).order_by(
        Purchase.created_at.desc()
    ).all()
    
    # Get user's sales
    sales = db.session.query(Purchase).join(SocialMediaAccount).filter(
        SocialMediaAccount.seller_id == current_user.id
    ).order_by(Purchase.created_at.desc()).all()
    
    return render_template('transactions/history.html', 
                         purchases=purchases,
                         sales=sales,
                         format_currency=format_currency)

@main_bp.route('/referral')
@login_required
def referral():
    referred_users = User.query.filter_by(referred_by_id=current_user.id).all()
    
    referral_url = url_for('auth.register', referral_code=current_user.referral_code, _external=True)
    
    return render_template('referral/referral.html', 
                         referred_users=referred_users,
                         referral_url=referral_url,
                         format_currency=format_currency)

@main_bp.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    form = SupportMessageForm()
    
    if form.validate_on_submit():
        message = SupportMessage(  # type: ignore
            user_id=current_user.id,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(message)
        db.session.commit()
        
        flash('Support message sent successfully. We will respond soon.', 'success')
        return redirect(url_for('main.support'))
    
    # Get user's previous messages
    messages = SupportMessage.query.filter_by(user_id=current_user.id).order_by(
        SupportMessage.created_at.desc()
    ).all()
    
    return render_template('support/chat.html', form=form, messages=messages)

@main_bp.route('/page/<slug>')
def footer_page(slug):
    page = FooterPage.query.filter_by(slug=slug, is_active=True).first_or_404()
    return render_template('footer/page.html', page=page)

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

@main_bp.route('/api/account-stats')
def api_account_stats():
    """API endpoint for account statistics"""
    platform = request.args.get('platform', '')
    
    query = SocialMediaAccount.query.filter_by(status='approved')
    if platform:
        query = query.filter_by(platform=platform)
    
    total = query.count()
    avg_price = db.session.query(func.avg(SocialMediaAccount.price)).filter_by(status='approved')
    if platform:
        avg_price = avg_price.filter_by(platform=platform)
    
    avg_price = avg_price.scalar() or 0
    
    return jsonify({
        'total_accounts': total,
        'average_price': round(avg_price, 2)
    })
