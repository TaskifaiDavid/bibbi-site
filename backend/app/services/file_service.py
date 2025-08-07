import os
from pathlib import Path
from fastapi import UploadFile
from app.services.db_service import DatabaseService
from app.utils.exceptions import FileProcessingException
from typing import Optional
import re

class FileService:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.db_service = DatabaseService()
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and ensure safe file storage"""
        if not filename:
            return "unnamed_file"
        
        # Get just the basename to prevent directory traversal
        clean_name = os.path.basename(filename)
        
        # Remove or replace dangerous characters, keep alphanumeric, dots, hyphens, underscores
        clean_name = re.sub(r'[^a-zA-Z0-9._-]', '_', clean_name)
        
        # Ensure filename doesn't start with dot (hidden files)
        if clean_name.startswith('.'):
            clean_name = 'file_' + clean_name[1:]
        
        # Limit filename length
        if len(clean_name) > 100:
            name_part, ext_part = os.path.splitext(clean_name)
            clean_name = name_part[:90] + ext_part
        
        # Ensure we have a valid filename
        if not clean_name or clean_name in ['.', '..']:
            clean_name = 'sanitized_file.txt'
        
        return clean_name
    
    async def save_upload(self, upload_id: str, file: UploadFile, user_id: str) -> str:
        try:
            # Sanitize filename for security
            safe_filename = self._sanitize_filename(file.filename)
            
            # Save file to disk with sanitized filename
            file_path = self.upload_dir / f"{upload_id}_{safe_filename}"
            
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Create database record with original filename for display, safe filename for storage
            await self.db_service.create_upload_record(
                upload_id=upload_id,
                user_id=user_id,
                filename=safe_filename,  # Store the sanitized filename
                file_size=len(contents)
            )
            
            return str(file_path)
        except Exception as e:
            raise FileProcessingException(f"Failed to save file: {str(e)}")
    
    async def get_file_path(self, upload_id: str, filename: str) -> Optional[Path]:
        # Sanitize filename for consistent path construction
        safe_filename = self._sanitize_filename(filename)
        file_path = self.upload_dir / f"{upload_id}_{safe_filename}"
        return file_path if file_path.exists() else None
    
    async def delete_file(self, upload_id: str, filename: str) -> bool:
        # Sanitize filename for consistent path construction
        safe_filename = self._sanitize_filename(filename)
        file_path = self.upload_dir / f"{upload_id}_{safe_filename}"
        if file_path.exists():
            os.remove(file_path)
            return True
        return False