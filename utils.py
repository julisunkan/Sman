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

def send_email_notification(to_email, subject, body):
    """Send email notification - placeholder for actual email service"""
    # In production, integrate with email service like SendGrid, Mailgun, etc.
    print(f"Email to {to_email}: {subject}")
    print(f"Body: {body}")
    return True

def calculate_referral_commission(amount, commission_rate=0.05):
    """Calculate referral commission"""
    return amount * commission_rate
