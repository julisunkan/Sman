import os
import secrets
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 15 * 1024  # 15KB - Target size after compression

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_path, max_size_kb=15, quality=85):
    """Compress image to specified size limit with aggressive compression"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            original_size = os.path.getsize(image_path)
            print(f"Compressing image: {os.path.basename(image_path)} (Original size: {original_size / 1024:.1f}KB)")
            
            # First, try to reduce quality without resizing
            for quality in range(quality, 5, -5):
                temp_path = image_path + '.tmp'
                img.save(temp_path, 'JPEG', quality=quality, optimize=True)
                
                file_size = os.path.getsize(temp_path)
                if file_size <= max_size_kb * 1024:
                    os.replace(temp_path, image_path)
                    print(f"Compressed to {file_size / 1024:.1f}KB using quality {quality}")
                    return True
                else:
                    os.remove(temp_path)
            
            # If quality reduction isn't enough, resize the image progressively
            width, height = img.size
            scale_factors = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            
            for scale_factor in scale_factors:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                # Ensure minimum size
                if new_width < 100 or new_height < 100:
                    continue
                    
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Try different quality levels for resized image
                for quality in [60, 50, 40, 30, 20]:
                    temp_path = image_path + '.tmp'
                    resized_img.save(temp_path, 'JPEG', quality=quality, optimize=True)
                    
                    file_size = os.path.getsize(temp_path)
                    if file_size <= max_size_kb * 1024:
                        os.replace(temp_path, image_path)
                        print(f"Compressed to {file_size / 1024:.1f}KB using {scale_factor*100:.0f}% size and quality {quality}")
                        return True
                    else:
                        os.remove(temp_path)
            
            print(f"Warning: Could not compress image to {max_size_kb}KB limit")
            return False
            
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

def save_file(file, folder):
    """Save uploaded file with automatic compression for oversized files"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, unique_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file initially
        file.save(file_path)
        
        # Handle different file types
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # For images, always try to compress to meet size limit
            original_size = os.path.getsize(file_path)
            
            if original_size > MAX_FILE_SIZE * 1024:
                print(f"File {filename} ({original_size / 1024:.1f}KB) exceeds limit, compressing...")
                
            # Always attempt compression to ensure file meets size requirements
            if compress_image(file_path):
                final_size = os.path.getsize(file_path)
                print(f"Successfully saved and compressed {filename} ({final_size / 1024:.1f}KB)")
                return os.path.join(folder, unique_filename)
            else:
                # If compression completely failed, still keep the file but log warning
                print(f"Warning: Could not compress {filename} to size limit, keeping original")
                return os.path.join(folder, unique_filename)
        
        elif filename.lower().endswith('.pdf'):
            # For PDF files, check size but accept larger files with warning
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE * 1024:
                print(f"Warning: PDF file {filename} ({file_size / 1024:.1f}KB) exceeds recommended {MAX_FILE_SIZE}KB limit")
                # Still accept the file but with a warning
            return os.path.join(folder, unique_filename)
        
        return os.path.join(folder, unique_filename)
    
    return None

def format_currency(amount):
    """Format currency for display in Naira"""
    return f"₦{amount:,.2f}"

def format_number(number):
    """Format large numbers (followers, etc.)"""
    if number >= 1000000:
        return f"{number/1000000:.1f}M"
    elif number >= 1000:
        return f"{number/1000:.1f}K"
    else:
        return str(number)

def send_email_notification(to_email, subject, body, template_name=None, template_data=None):
    """Send email notification with beautiful HTML templates"""
    from flask import render_template, current_app
    from models import SystemSettings
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Get email settings from admin configuration
        settings = {}
        email_settings = SystemSettings.query.filter(
            SystemSettings.setting_key.in_([
                'smtp_server', 'smtp_port', 'smtp_username', 'smtp_password', 
                'smtp_use_tls', 'from_email', 'from_name', 'site_name', 'site_description'
            ])
        ).all()
        
        for setting in email_settings:
            settings[setting.setting_key] = setting.setting_value
        
        # Get social links for email footer
        social_settings = SystemSettings.query.filter(
            SystemSettings.setting_key.in_([
                'facebook_url', 'twitter_url', 'instagram_url', 
                'telegram_url', 'linkedin_url', 'youtube_url'
            ])
        ).all()
        
        social_links = {}
        for setting in social_settings:
            if setting.setting_value:
                social_links[setting.setting_key] = setting.setting_value
        
        # Prepare template context
        template_context = {
            'subject': subject,
            'site_name': settings.get('site_name', 'SocialMarket'),
            'site_description': settings.get('site_description', 'Your trusted social media marketplace'),
            'social_links': social_links,
            'email_content': body
        }
        
        if template_data:
            template_context.update(template_data)
        
        # Render email template
        if template_name and template_name.endswith('.html'):
            try:
                html_body = render_template(f'emails/{template_name}', **template_context)
            except:
                # Fallback to base template
                html_body = render_template('emails/base_email.html', **template_context)
        else:
            # Use base template for simple emails
            html_body = render_template('emails/base_email.html', **template_context)
        
        # Check if SMTP is configured
        if not all([settings.get('smtp_server'), settings.get('smtp_username'), settings.get('smtp_password')]):
            print(f"Email to {to_email}: {subject}")
            print(f"HTML Body: {html_body[:200]}...")
            return True
        
        # Send actual email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.get('from_name', 'SocialMarket')} <{settings.get('from_email', settings.get('smtp_username'))}>"
        msg['To'] = to_email
        
        # Add plain text version
        text_part = MIMEText(body, 'plain')
        html_part = MIMEText(html_body, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        smtp_server = settings.get('smtp_server')
        smtp_port = int(settings.get('smtp_port', 587))
        smtp_username = settings.get('smtp_username')
        smtp_password = settings.get('smtp_password')
        
        if not smtp_server or not smtp_username or not smtp_password:
            raise Exception("Missing SMTP configuration")
            
        server = smtplib.SMTP(smtp_server, smtp_port)
        if settings.get('smtp_use_tls', 'true').lower() == 'true':
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email to {to_email}: {str(e)}")
        # Still log the email for debugging
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        return False

def calculate_referral_commission(amount, commission_rate=None):
    """Calculate referral commission using dynamic rate from settings"""
    if commission_rate is None:
        # Get rate from system settings
        from models import SystemSettings
        setting = SystemSettings.query.filter_by(setting_key='referral_rate').first()
        commission_rate = float(setting.setting_value) / 100 if setting and setting.setting_value else 0.05
    else:
        # If rate is passed as percentage, convert to decimal
        if commission_rate > 1:
            commission_rate = commission_rate / 100
    return amount * commission_rate
