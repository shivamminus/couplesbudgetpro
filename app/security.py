"""Security utilities and decorators"""
from functools import wraps
from flask import abort, request, current_app
from flask_login import current_user
import re

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def owner_required(model_class, id_field='id'):
    """Decorator to ensure user owns the resource"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            # Get the ID from kwargs
            resource_id = kwargs.get(id_field)
            if not resource_id:
                abort(400)
            
            # Check if resource exists and user owns it
            resource = model_class.query.get_or_404(resource_id)
            if resource.user_id != current_user.id:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_file_upload(file, allowed_extensions=None, max_size=None):
    """Validate uploaded files"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
    
    if max_size is None:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    
    if not file or file.filename == '':
        return False, 'No file selected'
    
    # Check file extension
    if '.' not in file.filename:
        return False, 'File must have an extension'
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    if extension not in allowed_extensions:
        return False, f'File type not allowed. Allowed: {", ".join(allowed_extensions)}'
    
    # Check file size (if we can)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Seek back to beginning
    
    if file_size > max_size:
        return False, f'File too large. Maximum size: {max_size // (1024*1024)}MB'
    
    return True, 'Valid file'

def sanitize_input(text, max_length=None):
    """Sanitize user input"""
    if not text:
        return ''
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length
    if max_length:
        text = text[:max_length]
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    return text

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number'
    
    return True, 'Password is valid'

def rate_limit_by_ip(max_requests=100, window=3600):
    """Simple rate limiting by IP address"""
    # This is a basic implementation - in production, use Redis or similar
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # For production, implement proper rate limiting with Redis
            # For now, just pass through
            return f(*args, **kwargs)
        return decorated_function
    return decorator
