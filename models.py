from datetime import datetime, timedelta
from app import db
from flask_login import UserMixin
from sqlalchemy import func
import secrets
import string

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, admin
    is_verified = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)  # Renamed from is_active to avoid UserMixin conflict
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile fields
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    country = db.Column(db.String(50))
    
    # KYC fields
    kyc_status = db.Column(db.String(20), default='pending')  # pending, verified, rejected
    kyc_document_path = db.Column(db.String(200))
    
    # Wallet
    balance = db.Column(db.Float, default=0.0)
    
    # Referral system
    referral_code = db.Column(db.String(10), unique=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_referral_earnings = db.Column(db.Float, default=0.0)
    
    # Email verification
    email_verification_token = db.Column(db.String(100))
    email_verification_expires = db.Column(db.DateTime)
    
    # Relationships
    accounts = db.relationship('SocialMediaAccount', backref='seller', lazy=True)
    purchases = db.relationship('Purchase', backref='buyer', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    referred_users = db.relationship('User', backref='referrer', remote_side=[id], lazy=True)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
    
    def generate_referral_code(self):
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not User.query.filter_by(referral_code=code).first():
                return code
    
    def generate_verification_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        return self.email_verification_token

class SocialMediaAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # instagram, tiktok, youtube, etc.
    username = db.Column(db.String(100), nullable=False)
    followers_count = db.Column(db.Integer)
    engagement_rate = db.Column(db.Float)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # lifestyle, business, entertainment, etc.
    
    # Account credentials (encrypted in production)
    login_email = db.Column(db.String(120))
    login_password = db.Column(db.String(200))
    
    # Status and verification
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, sold
    is_verified = db.Column(db.Boolean, default=False)
    verification_notes = db.Column(db.Text)
    
    # Seller information
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional media/proof
    screenshot_path = db.Column(db.String(200))
    
    # Relationships
    purchases = db.relationship('Purchase', backref='account', lazy=True)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('social_media_account.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled, refunded
    
    # Payment proof
    payment_proof_path = db.Column(db.String(200))
    payment_method = db.Column(db.String(50), default='bank_transfer')
    
    # Admin verification
    verified_by_admin = db.Column(db.Boolean, default=False)
    admin_notes = db.Column(db.Text)
    
    # Account details released
    details_released = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    transaction_type = db.Column(db.String(50), nullable=False)  # deposit, purchase, referral_earning, withdrawal
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    
    # For deposit transactions
    payment_proof_path = db.Column(db.String(200))
    admin_verified = db.Column(db.Boolean, default=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, completed, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FooterPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, closed
    admin_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='support_messages')
