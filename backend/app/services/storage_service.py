"""Document storage: Google Cloud Storage in deployment, local filesystem fallback for development."""

import logging
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import Settings

logger = logging.getLogger(__name__)


def build_storage_key(user_id: str, extension: str) -> str:
    """Randomized object key; never derived from the user-supplied filename."""
    return f"documents/{user_id}/{uuid.uuid4().hex}{extension}"


class StorageService(ABC):
    @abstractmethod
    def upload(self, key: str, content: bytes, content_type: str) -> None: ...

    @abstractmethod
    def download(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalStorageService(StorageService):
    def __init__(self, root: str) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if self._root not in path.parents:
            raise ValueError("Invalid storage key")
        return path

    def upload(self, key: str, content: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def download(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()


class GcsStorageService(StorageService):
    def __init__(self, bucket_name: str, project_id: str | None) -> None:
        from google.cloud import storage

        self._client = storage.Client(project=project_id)
        self._bucket = self._client.bucket(bucket_name)

    def upload(self, key: str, content: bytes, content_type: str) -> None:
        self._bucket.blob(key).upload_from_string(content, content_type=content_type)

    def download(self, key: str) -> bytes:
        return self._bucket.blob(key).download_as_bytes()

    def delete(self, key: str) -> None:
        blob = self._bucket.blob(key)
        if blob.exists():
            blob.delete()


def build_storage_service(settings: Settings) -> StorageService:
    if settings.uses_gcs:
        logger.info("Using Google Cloud Storage bucket for document storage")
        return GcsStorageService(settings.gcs_bucket, settings.gcp_project_id)
    logger.info("Using local filesystem storage (development fallback)")
    return LocalStorageService(settings.local_storage_dir)
