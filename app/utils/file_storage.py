import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename: str) -> bool:
    """Check if file extension is within allowed administrative document types."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file_storage, custom_prefix='doc') -> tuple[str, str, str, int, str]:
    """
    Saves uploaded file securely.
    Returns: (original_filename, stored_filename, full_saved_path, file_size_bytes, mime_type)
    """
    original_filename = secure_filename(file_storage.filename or 'document')
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'
    
    # Generate unique stored filename to prevent overwrites and directory traversal
    stored_filename = f"{custom_prefix}_{uuid.uuid4().hex[:12]}.{ext}"
    
    upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
    upload_folder.mkdir(parents=True, exist_ok=True)
    
    target_path = upload_folder / stored_filename
    file_storage.save(target_path)
    
    file_size = target_path.stat().st_size
    mime_type = file_storage.content_type or 'application/octet-stream'
    
    return original_filename, stored_filename, str(target_path), file_size, mime_type
