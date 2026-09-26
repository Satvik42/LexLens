"""Upload validation. Uploaded files are untrusted: validate extension, MIME, magic bytes, size and filename."""

import re
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath

from fastapi import HTTPException, status

SUPPORTED_TYPES: dict[str, tuple[str, ...]] = {
    "application/pdf": (".pdf",),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (".docx",),
    "text/plain": (".txt",),
}
EXTENSION_TO_MIME = {ext: mime for mime, exts in SUPPORTED_TYPES.items() for ext in exts}

_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._ -]+")
_MAX_FILENAME_LENGTH = 120


class UploadValidationError(HTTPException):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": code, "message": message})


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    mime_type: str
    extension: str
    content: bytes


def sanitize_filename(raw_name: str | None) -> str:
    """Strip directories, control characters and unsafe symbols from a user-supplied filename."""
    name = PurePosixPath((raw_name or "").replace("\\", "/")).name
    name = _FILENAME_SAFE.sub("_", name).strip(" ._") or "document"
    if len(name) > _MAX_FILENAME_LENGTH:
        stem, dot, ext = name.rpartition(".")
        keep = _MAX_FILENAME_LENGTH - len(ext) - 1
        name = f"{stem[:keep]}{dot}{ext}" if dot else name[:_MAX_FILENAME_LENGTH]
    return name


def _extension_of(filename: str) -> str:
    return PurePosixPath(filename.lower()).suffix


def _looks_like_pdf(content: bytes) -> bool:
    return content[:5] == b"%PDF-"


def _looks_like_docx(content: bytes) -> bool:
    if content[:4] != b"PK\x03\x04":
        return False
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            return "word/document.xml" in archive.namelist()
    except zipfile.BadZipFile:
        return False


def _looks_like_text(content: bytes) -> bool:
    if b"\x00" in content:
        return False
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


_SNIFFERS = {
    ".pdf": _looks_like_pdf,
    ".docx": _looks_like_docx,
    ".txt": _looks_like_text,
}


def validate_upload(raw_filename: str | None, declared_mime: str | None, content: bytes, max_bytes: int) -> ValidatedUpload:
    filename = sanitize_filename(raw_filename)
    extension = _extension_of(filename)

    if extension not in EXTENSION_TO_MIME:
        raise UploadValidationError("UNSUPPORTED_TYPE", "Only PDF, DOCX and TXT files are supported.")

    expected_mime = EXTENSION_TO_MIME[extension]
    declared = (declared_mime or "").split(";")[0].strip().lower()
    if declared and declared not in SUPPORTED_TYPES and declared != "application/octet-stream":
        raise UploadValidationError("UNSUPPORTED_TYPE", "The file type does not match a supported document format.")
    if declared in SUPPORTED_TYPES and declared != expected_mime:
        raise UploadValidationError("MIME_MISMATCH", "The file extension does not match its content type.")

    if len(content) == 0:
        raise UploadValidationError("EMPTY_FILE", "The uploaded file is empty.")
    if len(content) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        raise UploadValidationError("FILE_TOO_LARGE", f"Files must be smaller than {limit_mb} MB.")

    if not _SNIFFERS[extension](content):
        raise UploadValidationError("CONTENT_MISMATCH", "The file content does not look like a valid document of this type.")

    return ValidatedUpload(filename=filename, mime_type=expected_mime, extension=extension, content=content)
