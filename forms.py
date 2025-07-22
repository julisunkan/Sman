from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, FloatField, SelectField, IntegerField, PasswordField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, Optional
from models import User, SocialMediaAccount

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    referral_code = StringField('Referral Code (Optional)', validators=[Optional()])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    country = StringField('Country', validators=[DataRequired(), Length(max=50)])

class KYCForm(FlaskForm):
    document = FileField('Identity Document', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDF files only!')
    ])

class SocialMediaAccountForm(FlaskForm):
    platform = SelectField('Platform', choices=[
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter/X'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('snapchat', 'Snapchat'),
        ('telegram', 'Telegram')
    ], validators=[DataRequired()])
    
    username = StringField('Username/Handle', validators=[DataRequired(), Length(max=100)])
    followers_count = IntegerField('Followers Count', validators=[DataRequired(), NumberRange(min=0)])
    engagement_rate = FloatField('Engagement Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    price = FloatField('Price ($)', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    
    category = SelectField('Category', choices=[
        ('lifestyle', 'Lifestyle'),
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('technology', 'Technology'),
        ('fashion', 'Fashion'),
        ('food', 'Food & Cooking'),
        ('travel', 'Travel'),
        ('fitness', 'Fitness & Health'),
        ('education', 'Education'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    login_email = StringField('Account Email', validators=[DataRequired(), Email()])
    login_password = StringField('Account Password', validators=[DataRequired()])
    
    screenshot = FileField('Account Screenshot', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])

class DepositForm(FlaskForm):
    amount = FloatField('Deposit Amount ($)', validators=[DataRequired(), NumberRange(min=10)])
    payment_proof = FileField('Payment Proof', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDF files only!')
    ])

class PurchaseForm(FlaskForm):
    account_id = HiddenField('Account ID', validators=[DataRequired()])
    payment_proof = FileField('Payment Proof', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Images and PDF files only!')
    ])

class AdminAccountVerificationForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    verification_notes = TextAreaField('Notes', validators=[Optional()])

class AdminPaymentVerificationForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('completed', 'Approved'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Optional()])

class AdminUserManagementForm(FlaskForm):
    active = BooleanField('Active')
    kyc_status = SelectField('KYC Status', choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ])

class FooterPageForm(FlaskForm):
    title = StringField('Page Title', validators=[DataRequired(), Length(max=100)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(max=100)])
    content = TextAreaField('Content (HTML)', validators=[DataRequired()])
    active = BooleanField('Active')

class SupportMessageForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])

class SearchForm(FlaskForm):
    platform = SelectField('Platform', choices=[
        ('', 'All Platforms'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter/X'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('snapchat', 'Snapchat'),
        ('telegram', 'Telegram')
    ], validators=[Optional()])
    
    category = SelectField('Category', choices=[
        ('', 'All Categories'),
        ('lifestyle', 'Lifestyle'),
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('technology', 'Technology'),
        ('fashion', 'Fashion'),
        ('food', 'Food & Cooking'),
        ('travel', 'Travel'),
        ('fitness', 'Fitness & Health'),
        ('education', 'Education'),
        ('other', 'Other')
    ], validators=[Optional()])
    
    min_price = FloatField('Min Price', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[Optional(), NumberRange(min=0)])
    min_followers = IntegerField('Min Followers', validators=[Optional(), NumberRange(min=0)])
