import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Register blueprints
from auth import auth_bp
from admin import admin_bp
from routes import main_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(main_bp)

# Create uploads directory
os.makedirs('uploads', exist_ok=True)
os.makedirs('uploads/payment_proofs', exist_ok=True)
os.makedirs('uploads/kyc_documents', exist_ok=True)

with app.app_context():
    # Import models to ensure they're registered
    import models
    db.create_all()
    
    # Create admin user if it doesn't exist
    from models import User, FooterPage
    from werkzeug.security import generate_password_hash
    
    admin_user = User.query.filter_by(email='admin@marketplace.com').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@marketplace.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_verified=True,
            active=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: admin@marketplace.com / admin123")
    
    # Create default footer pages if they don't exist
    default_pages = [
        {
            'title': 'Privacy Policy',
            'slug': 'privacy',
            'content': '''
<h2>Privacy Policy</h2>
<p><strong>Last updated:</strong> January 2025</p>

<h3>Information We Collect</h3>
<p>We collect information you provide directly to us, such as when you create an account, make a purchase, or contact us for support. This includes:</p>
<ul>
<li>Personal information (name, email address, phone number)</li>
<li>Account credentials and KYC documents</li>
<li>Payment information and transaction history</li>
<li>Communications with our support team</li>
</ul>

<h3>How We Use Your Information</h3>
<p>We use the information we collect to:</p>
<ul>
<li>Provide, maintain, and improve our marketplace services</li>
<li>Process transactions and verify payments</li>
<li>Verify user identity and prevent fraud</li>
<li>Communicate with you about your account and transactions</li>
<li>Provide customer support</li>
</ul>

<h3>Information Sharing</h3>
<p>We do not sell, trade, or rent your personal information to third parties without your consent. We may share information only:</p>
<ul>
<li>With your explicit consent</li>
<li>To comply with legal requirements</li>
<li>To protect our rights and prevent fraud</li>
<li>In connection with a business transfer</li>
</ul>

<h3>Data Security</h3>
<p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. However, no method of transmission over the internet is 100% secure.</p>

<h3>Your Rights</h3>
<p>You have the right to:</p>
<ul>
<li>Access and update your personal information</li>
<li>Request deletion of your account and data</li>
<li>Opt out of marketing communications</li>
<li>Request a copy of your data</li>
</ul>

<h3>Contact Us</h3>
<p>If you have any questions about this Privacy Policy, please contact us at privacy@socialmarket.com</p>
            ''',
            'is_active': True
        },
        {
            'title': 'Terms of Service',
            'slug': 'terms',
            'content': '''
<h2>Terms of Service</h2>
<p><strong>Last updated:</strong> January 2025</p>

<h3>Acceptance of Terms</h3>
<p>By using SocialMarket, you agree to be bound by these Terms of Service and our Privacy Policy. If you do not agree to these terms, please do not use our service.</p>

<h3>Description of Service</h3>
<p>SocialMarket is an online marketplace that facilitates the buying and selling of social media accounts. We provide a platform for users to list, browse, and transact social media accounts securely.</p>

<h3>User Accounts</h3>
<p>To use our service, you must:</p>
<ul>
<li>Be at least 18 years old</li>
<li>Provide accurate and complete information</li>
<li>Maintain the confidentiality of your account credentials</li>
<li>Be responsible for all activities under your account</li>
<li>Complete identity verification (KYC) for selling accounts</li>
</ul>

<h3>Prohibited Activities</h3>
<p>You may not:</p>
<ul>
<li>Engage in fraudulent transactions or misrepresent account details</li>
<li>Sell fake, inactive, or compromised accounts</li>
<li>Violate any applicable laws or regulations</li>
<li>Harass, threaten, or abuse other users</li>
<li>Attempt to circumvent our security measures</li>
<li>Use our service for money laundering or other illegal activities</li>
</ul>

<h3>Account Trading Rules</h3>
<p>All social media accounts must be:</p>
<ul>
<li>Legitimately owned by the seller</li>
<li>Transferred with accurate login credentials</li>
<li>Free from violations of the respective platform's terms</li>
<li>Accurately described with correct follower counts and engagement rates</li>
</ul>

<h3>Payment Terms</h3>
<p>All transactions are subject to admin verification. Payments must be made through approved methods only. Refunds are processed according to our refund policy and only in cases of verified fraud or misrepresentation.</p>

<h3>Fees and Commissions</h3>
<p>We charge fees for our services as disclosed during the transaction process. Referral commissions are paid according to our referral program terms.</p>

<h3>Disclaimers</h3>
<p>We provide our marketplace "as is" without warranties. We are not responsible for the actions of users or the performance of social media accounts after transfer.</p>

<h3>Limitation of Liability</h3>
<p>Our liability is limited to the maximum extent permitted by law. We are not liable for indirect, incidental, or consequential damages.</p>

<h3>Termination</h3>
<p>We reserve the right to terminate accounts that violate these terms or engage in prohibited activities.</p>

<h3>Contact Information</h3>
<p>For questions about these terms, contact us at legal@socialmarket.com</p>
            ''',
            'is_active': True
        },
        {
            'title': 'Cookie Policy',
            'slug': 'cookies',
            'content': '''
<h2>Cookie Policy</h2>
<p><strong>Last updated:</strong> January 2025</p>

<h3>What Are Cookies</h3>
<p>Cookies are small text files that are placed on your computer or mobile device when you visit our website. They are widely used to make websites work more efficiently and provide information to website owners.</p>

<h3>How We Use Cookies</h3>
<p>We use cookies for several purposes:</p>

<h4>Essential Cookies</h4>
<p>These cookies are necessary for our website to function properly. They enable basic features like page navigation, access to secure areas, and remembering your login status.</p>

<h4>Analytics Cookies</h4>
<p>These cookies help us understand how visitors interact with our website by collecting and reporting information anonymously. This helps us improve our service.</p>

<h4>Preference Cookies</h4>
<p>These cookies allow our website to remember information that changes the way the website behaves or looks, such as your preferred language or region.</p>

<h4>Security Cookies</h4>
<p>These cookies help us detect suspicious activity and protect against fraud. They are essential for maintaining the security of our marketplace.</p>

<h3>Types of Cookies We Use</h3>
<ul>
<li><strong>Session Cookies:</strong> Temporary cookies that expire when you close your browser</li>
<li><strong>Persistent Cookies:</strong> Cookies that remain on your device for a set period</li>
<li><strong>First-party Cookies:</strong> Cookies set by our website</li>
<li><strong>Third-party Cookies:</strong> Cookies set by external services we use</li>
</ul>

<h3>Managing Cookies</h3>
<p>You can control and/or delete cookies as you wish. You can delete all cookies that are already on your computer and you can set most browsers to prevent them from being placed.</p>

<p>However, if you do not accept cookies, you may not be able to use some portions of our service.</p>

<h4>Browser Settings</h4>
<p>Most web browsers allow you to:</p>
<ul>
<li>See what cookies are stored on your device</li>
<li>Delete cookies individually or all at once</li>
<li>Block cookies from specific sites</li>
<li>Block all cookies</li>
<li>Get notifications when cookies are set</li>
</ul>

<h3>Third-Party Cookies</h3>
<p>We may use third-party services that place cookies on your device to help us:</p>
<ul>
<li>Analyze website usage and performance</li>
<li>Provide customer support features</li>
<li>Process payments securely</li>
<li>Prevent fraud and maintain security</li>
</ul>

<h3>Updates to This Policy</h3>
<p>We may update this Cookie Policy from time to time. Any changes will be posted on this page with an updated "Last updated" date.</p>

<h3>Contact Us</h3>
<p>If you have questions about our use of cookies, please contact us at privacy@socialmarket.com</p>
            ''',
            'is_active': True
        }
    ]
    
    for page_data in default_pages:
        existing_page = FooterPage.query.filter_by(slug=page_data['slug']).first()
        if not existing_page:
            page = FooterPage()
            page.title = page_data['title']
            page.slug = page_data['slug']
            page.content = page_data['content']
            page.is_active = page_data['is_active']
            db.session.add(page)
    
    db.session.commit()
    print("Default footer pages created")
