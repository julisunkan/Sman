import os
import secrets
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 15 * 1024  # 15KB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_path, max_size_kb=15, quality=85):
    """Compress image to specified size limit"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Try different quality settings to meet size requirement
            for quality in range(quality, 10, -5):
                # Save to temporary path
                temp_path = image_path + '.tmp'
                img.save(temp_path, 'JPEG', quality=quality, optimize=True)
                
                # Check file size
                file_size = os.path.getsize(temp_path)
                if file_size <= max_size_kb * 1024:
                    # Replace original with compressed version
                    os.replace(temp_path, image_path)
                    return True
                else:
                    os.remove(temp_path)
            
            # If still too large, resize the image
            width, height = img.size
            scale_factor = 0.8
            
            while True:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                temp_path = image_path + '.tmp'
                resized_img.save(temp_path, 'JPEG', quality=70, optimize=True)
                
                file_size = os.path.getsize(temp_path)
                if file_size <= max_size_kb * 1024:
                    os.replace(temp_path, image_path)
                    return True
                else:
                    os.remove(temp_path)
                    scale_factor -= 0.1
                    if scale_factor <= 0.1:
                        break
            
            return False
            
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

def save_file(file, folder):
    """Save uploaded file with compression if needed"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, unique_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        file.save(file_path)
        
        # Compress if it's an image
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            if compress_image(file_path):
                return os.path.join(folder, unique_filename)
            else:
                # If compression failed, remove file and return None
                os.remove(file_path)
                return None
        
        # For PDF files, check size
        if filename.lower().endswith('.pdf'):
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE * 1024:
                os.remove(file_path)
                return None
        
        return os.path.join(folder, unique_filename)
    
    return None

def format_currency(amount):
    """Format currency for display"""
    return f"${amount:,.2f}"

def format_number(number):
    """Format large numbers (followers, etc.)"""
    if number >= 1000000:
        return f"{number/1000000:.1f}M"
    elif number >= 1000:
        return f"{number/1000:.1f}K"
    else:
        return str(number)

def send_email_notification(to_email, subject, body):
    """Send email notification - placeholder for actual email service"""
    # In production, integrate with email service like SendGrid, Mailgun, etc.
    print(f"Email to {to_email}: {subject}")
    print(f"Body: {body}")
    return True

def calculate_referral_commission(amount, commission_rate=0.05):
    """Calculate referral commission"""
    return amount * commission_rate
