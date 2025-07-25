from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, FloatField, IntegerField, BooleanField, PasswordField, EmailField, SubmitField, URLField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, EqualTo, ValidationError, URL
from wtforms.widgets import TextArea

# Authentication Forms
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    referral_code = StringField('Referral Code (Optional)', validators=[Optional(), Length(max=10)])
    submit = SubmitField('Register')

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    country = StringField('Country', validators=[Optional(), Length(max=50)])

class KYCForm(FlaskForm):
    document = FileField('Identity Document', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only JPG, PNG and PDF files are allowed!')
    ])

class SocialMediaAccountForm(FlaskForm):
    platform = SelectField('Platform', choices=[
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('snapchat', 'Snapchat'),
        ('telegram', 'Telegram')
    ], validators=[DataRequired()])
    username = StringField('Username (without @)', validators=[DataRequired(), Length(min=1, max=100)])
    followers_count = IntegerField('Followers Count', validators=[DataRequired(), NumberRange(min=1)])
    engagement_rate = FloatField('Engagement Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    price = FloatField('Price (₦)', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('lifestyle', 'Lifestyle'),
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('technology', 'Technology'),
        ('fashion', 'Fashion'),
        ('food', 'Food'),
        ('travel', 'Travel'),
        ('fitness', 'Fitness'),
        ('education', 'Education'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    login_email = EmailField('Account Login Email', validators=[DataRequired(), Email()])
    login_password = PasswordField('Account Login Password', validators=[DataRequired(), Length(min=6)])
    account_url = URLField('Account URL (for preview)', validators=[Optional(), URL()])
    screenshot = FileField('Account Screenshot', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG and PNG files are allowed!')
    ])

class DepositForm(FlaskForm):
    amount = FloatField('Amount (₦)', validators=[DataRequired(), NumberRange(min=1)])
    payment_proof = FileField('Payment Proof', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only JPG, PNG and PDF files are allowed!')
    ])

class WithdrawalForm(FlaskForm):
    amount = FloatField('Amount (₦)', validators=[DataRequired(), NumberRange(min=1)])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(min=2, max=100)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(min=10, max=20)])
    account_name = StringField('Account Name', validators=[DataRequired(), Length(min=2, max=100)])
    
    def validate_amount(self, field):
        from flask_login import current_user
        if field.data > current_user.balance:
            raise ValidationError('Insufficient balance. Your current balance is ₦{:,.2f}'.format(current_user.balance))

# Admin Forms
class AdminEditAccountForm(FlaskForm):
    platform = SelectField('Platform', choices=[
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('snapchat', 'Snapchat'),
        ('telegram', 'Telegram')
    ], validators=[DataRequired()])
    username = StringField('Username (without @)', validators=[DataRequired(), Length(min=1, max=100)])
    followers_count = IntegerField('Followers Count', validators=[DataRequired(), NumberRange(min=1)])
    engagement_rate = FloatField('Engagement Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    price = FloatField('Price (₦)', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    category = SelectField('Category', choices=[
        ('lifestyle', 'Lifestyle'),
        ('business', 'Business'),
        ('entertainment', 'Entertainment'),
        ('sports', 'Sports'),
        ('technology', 'Technology'),
        ('fashion', 'Fashion'),
        ('food', 'Food'),
        ('travel', 'Travel'),
        ('fitness', 'Fitness'),
        ('education', 'Education'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    account_url = URLField('Account URL (for preview)', validators=[Optional(), URL()])
    login_email = EmailField('Account Login Email', validators=[DataRequired(), Email()])
    login_password = StringField('Account Login Password', validators=[DataRequired(), Length(min=6)])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('sold', 'Sold')
    ], validators=[DataRequired()])
    verification_notes = TextAreaField('Verification Notes', validators=[Optional(), Length(max=1000)])

class PurchaseForm(FlaskForm):
    account_id = IntegerField('Account ID', validators=[DataRequired()])

class SupportMessageForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=2000)])

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    platform = SelectField('Platform', choices=[
        ('', 'All Platforms'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter'),
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
        ('food', 'Food'),
        ('travel', 'Travel'),
        ('fitness', 'Fitness'),
        ('education', 'Education'),
        ('other', 'Other')
    ], validators=[Optional()])
    min_price = FloatField('Min Price (₦)', validators=[Optional(), NumberRange(min=0)])
    max_price = FloatField('Max Price (₦)', validators=[Optional(), NumberRange(min=0)])
    min_followers = IntegerField('Min Followers', validators=[Optional(), NumberRange(min=0)])

# Admin Forms
class AdminAccountVerificationForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('approved', 'Approve'),
        ('rejected', 'Reject')
    ], validators=[DataRequired()])
    verification_notes = TextAreaField('Verification Notes', validators=[Optional(), Length(max=500)])

class AdminPaymentVerificationForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('completed', 'Approve Payment'),
        ('rejected', 'Reject Payment')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Optional(), Length(max=500)])

class AdminDepositVerificationForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('completed', 'Approve Deposit'),
        ('rejected', 'Reject Deposit')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Optional(), Length(max=500)])

class AdminWithdrawalForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('approved', 'Approve Withdrawal'),
        ('rejected', 'Reject Withdrawal'),
        ('paid', 'Mark as Paid')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Admin Notes', validators=[Optional(), Length(max=500)])

class AdminUserManagementForm(FlaskForm):
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    is_verified = BooleanField('Email Verified')
    active = BooleanField('Account Active')
    kyc_status = SelectField('KYC Status', choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    balance = FloatField('Wallet Balance (₦)', validators=[Optional(), NumberRange(min=0)])

class AdminCreateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    is_verified = BooleanField('Email Verified', default=True)
    active = BooleanField('Account Active', default=True)
    balance = FloatField('Initial Balance (₦)', validators=[Optional(), NumberRange(min=0)], default=0)
    kyc_status = SelectField('KYC Status', choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], default='pending')
    submit = SubmitField('Create User')

class FooterPageForm(FlaskForm):
    title = StringField('Page Title', validators=[DataRequired(), Length(min=2, max=100)])
    slug = StringField('URL Slug', validators=[DataRequired(), Length(min=2, max=100)])
    content = TextAreaField('Page Content', validators=[DataRequired()], widget=TextArea())
    is_active = BooleanField('Published', default=True)
    submit = SubmitField('Save Page')

class SystemSettingsForm(FlaskForm):
    # Bank Details
    bank_name = StringField('Bank Name', validators=[Optional(), Length(max=100)])
    account_number = StringField('Account Number', validators=[Optional(), Length(max=20)])
    account_name = StringField('Account Name', validators=[Optional(), Length(max=100)])
    
    # SMTP Settings
    smtp_server = StringField('SMTP Server', validators=[Optional(), Length(max=100)])
    smtp_port = IntegerField('SMTP Port', validators=[Optional(), NumberRange(min=1, max=65535)])
    smtp_username = StringField('SMTP Username', validators=[Optional(), Length(max=100)])
    smtp_password = PasswordField('SMTP Password', validators=[Optional()])
    smtp_use_tls = BooleanField('Use TLS', default=True)
    from_email = EmailField('From Email', validators=[Optional(), Email()])
    from_name = StringField('From Name', validators=[Optional(), Length(max=100)])
    
    # General Settings
    site_name = StringField('Site Name', validators=[Optional(), Length(max=100)])
    site_description = TextAreaField('Site Description', validators=[Optional(), Length(max=500)])
    commission_rate = FloatField('Commission Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    referral_rate = FloatField('Referral Commission Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)])
    min_deposit = FloatField('Minimum Deposit (₦)', validators=[Optional(), NumberRange(min=1)])
    max_file_size = IntegerField('Max File Size (MB)', validators=[Optional(), NumberRange(min=1, max=100)])
    
    # Social Media Links
    facebook_url = URLField('Facebook URL', validators=[Optional(), URL()])
    twitter_url = URLField('Twitter URL', validators=[Optional(), URL()])
    instagram_url = URLField('Instagram URL', validators=[Optional(), URL()])
    telegram_url = URLField('Telegram URL', validators=[Optional(), URL()])
    linkedin_url = URLField('LinkedIn URL', validators=[Optional(), URL()])
    youtube_url = URLField('YouTube URL', validators=[Optional(), URL()])

class TestEmailForm(FlaskForm):
    test_email = EmailField('Test Email Address', validators=[DataRequired(), Email()])
    subject = StringField('Test Subject', validators=[DataRequired()], default='Test Email from SocialMarket')
    message = TextAreaField('Test Message', validators=[DataRequired()], default='This is a test email to verify SMTP configuration.')
    submit = SubmitField('Send Test Email')

class AdminSupportResponseForm(FlaskForm):
    response = TextAreaField('Response', validators=[DataRequired()], 
                           render_kw={'rows': 6, 'placeholder': 'Type your response here...'})
    submit = SubmitField('Send Response & Close Ticket')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')
    
    def validate_current_password(self, field):
        from flask_login import current_user
        from werkzeug.security import check_password_hash
        if not check_password_hash(current_user.password_hash, field.data):
            raise ValidationError('Current password is incorrect.')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class SettingsImportForm(FlaskForm):
    settings_file = FileField('Settings File (JSON)', validators=[
        DataRequired(),
        FileAllowed(['json'], 'Only JSON files are allowed!')
    ])
    overwrite_existing = BooleanField('Overwrite Existing Settings', default=False)
    submit = SubmitField('Import Settings')

class SettingsExportForm(FlaskForm):
    export_type = SelectField('Export Type', choices=[
        ('all', 'All Settings'),
        ('bank', 'Bank Details Only'),
        ('smtp', 'SMTP Settings Only'),
        ('general', 'General Settings Only'),
        ('social', 'Social Media Links Only')
    ], validators=[DataRequired()], default='all')
    submit = SubmitField('Export Settings')