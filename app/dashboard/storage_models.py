from dataclasses import dataclass
from typing import BinaryIO


@dataclass
class FileToUpload:
    filename: str
    content_type: str
    file_size: int
    stream: BinaryIO

@dataclass
class UploadedFileInfo:
    filename: str
    s3_key: str
    content_type: str
    file_size: int

@dataclass
class FileToUpdate:
    filename:str
    s3_key: str
    content_type: str
    stream: BinaryIO


