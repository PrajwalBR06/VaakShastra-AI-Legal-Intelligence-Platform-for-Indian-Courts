"""
File storage service - local filesystem only (no boto3/S3 needed).
"""

import os
import aiofiles
from pathlib import Path

from app.config import settings


class StorageService:
    def __init__(self):
        self.upload_dir = Path(settings.local_upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _generate_path(self, user_id: str, document_id: str, filename: str) -> str:
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
        return f"{user_id}/{document_id}/{safe_name}"

    async def upload_file(self, file_content: bytes, user_id: str, document_id: str, filename: str, content_type: str = "application/pdf") -> str:
        storage_path = self._generate_path(user_id, document_id, filename)
        full_path = self.upload_dir / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_content)

        return str(storage_path)

    async def download_file(self, storage_path: str):
        full_path = self.upload_dir / storage_path
        if not full_path.exists():
            return None
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete_file(self, storage_path: str) -> bool:
        full_path = self.upload_dir / storage_path
        if full_path.exists():
            os.remove(full_path)
            return True
        return False


storage_service = StorageService()
