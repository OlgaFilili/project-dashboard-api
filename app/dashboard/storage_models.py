from dataclasses import dataclass


@dataclass
class FileUploadRequest:
    filename: str
    content_type: str


@dataclass
class UploadInfo:
    filename: str
    s3_key: str
    upload_url: str
    content_type: str


@dataclass
class FileMetadata:
    content_type: str
    file_size: int


@dataclass
class UploadedFileInfo:
    filename: str
    s3_key: str
    content_type: str
    file_size: int


@dataclass
class FileUpdateRequest:
    s3_key: str
    content_type: str
