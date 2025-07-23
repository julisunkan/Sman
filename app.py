import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-123")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
if os.environ.get("DATABASE_URL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # Use SQLite for development with absolute path for reliability
    db_path = os.path.abspath("instance/marketplace.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directories exist
os.makedirs('uploads/kyc_documents', exist_ok=True)
os.makedirs('uploads/payment_proofs', exist_ok=True)

# Initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize Flask-WTF for CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Context processor to make site data available in all templates
@app.context_processor
def inject_site_data():
    from models import FooterPage, SystemSettings
    footer_pages = FooterPage.query.filter_by(is_active=True).order_by(FooterPage.title).all()
    
    # Get all system settings
    all_settings = SystemSettings.query.all()
    settings_dict = {s.setting_key: s.setting_value for s in all_settings}
    
    # Extract social media settings
    social_links = {k: v for k, v in settings_dict.items() if k.endswith('_url')}
    
    # Site configuration
    site_config = {
        'site_name': settings_dict.get('site_name', 'SocialMarket'),
        'site_description': settings_dict.get('site_description', 'The trusted marketplace for buying and selling social media accounts safely and securely.')
    }
    
    return {
        'footer_pages': footer_pages,
        'social_links': social_links,
        'site_config': site_config
    }

# Import blueprints
from auth import auth_bp
from admin import admin_bp
from routes import main_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(main_bp)

with app.app_context():
    # Import models to ensure tables are created
    from models import User, SocialMediaAccount, Transaction, SupportMessage, Purchase, FooterPage
    
    # Only create tables if they don't exist
    db.create_all()
    
    # Create default admin user if it doesn't exist
    from werkzeug.security import generate_password_hash
    
    admin_user = User.query.filter_by(email='admin@marketplace.com').first() or User.query.filter_by(role='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@marketplace.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_verified=True,
            active=True,
            full_name='System Administrator'
        )
        db.session.add(admin_user)
    
    # Create default footer pages if they don't exist
    pages_to_create = [
        {'slug': 'privacy-policy', 'title': 'Privacy Policy', 'content': '<h2>Privacy Policy</h2><p>This is the privacy policy page. Content will be added soon.</p>'},
        {'slug': 'terms-of-service', 'title': 'Terms of Service', 'content': '<h2>Terms of Service</h2><p>This is the terms of service page. Content will be added soon.</p>'},
        {'slug': 'cookie-policy', 'title': 'Cookie Policy', 'content': '<h2>Cookie Policy</h2><p>This is the cookie policy page. Content will be added soon.</p>'}
    ]
    
    for page_data in pages_to_create:
        existing_page = FooterPage.query.filter_by(slug=page_data['slug']).first()
        if not existing_page:
            page = FooterPage(  # type: ignore
                slug=page_data['slug'],
                title=page_data['title'],
                content=page_data['content']
            )
            db.session.add(page)
    
    try:
        db.session.commit()
        print("Default admin user and footer pages created")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating defaults: {e}")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500