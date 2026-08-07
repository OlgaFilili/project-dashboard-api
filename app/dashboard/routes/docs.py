from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.exceptions import (
    DocumentNotFoundError,
    FileMetadataMismatchError,
    NoAccessError,
    ProjectNotFoundError,
    UnsupportedFileTypeError,
    UploadedFileNotFoundError,
)
from app.dashboard.schemas import (
    DocResponse,
    DocsResponse,
    FileRequest,
    StoragesRequest,
    UpdateRequest,
    UpdateResponse,
    UploadsRequest,
    UploadsResponse,
)
from app.dashboard.service.docs import (
    add_documents,
    del_document,
    get_document,
    prepare_for_update,
    prepare_for_uploads,
    put_document,
)
from app.dashboard.service.security import get_current_user
from app.database.db import get_session
from app.database.models import User

router = APIRouter(tags=["documents"])


@router.post("/project/{project_id}/documents", response_model=UploadsResponse, status_code=200)
async def upload_documents_request(project_id: int, request: UploadsRequest, user: User = Depends(get_current_user),
                           async_session: AsyncSession = Depends(get_session)) -> UploadsResponse:
    try:
        return await prepare_for_uploads(async_session, project_id, user.id, request)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the project")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except UnsupportedFileTypeError:
        raise HTTPException(status_code=415, detail="File type not supported")


@router.post("/project/{project_id}/documents/complete", response_model=DocsResponse, status_code=201)
async def upload_documents(project_id: int, request: StoragesRequest, user: User = Depends(get_current_user),
                           async_session: AsyncSession = Depends(get_session)) -> DocsResponse:
    try:
        return await add_documents(async_session, project_id, user.id, request)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the project")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except UnsupportedFileTypeError:
        raise HTTPException(status_code=415, detail="File type not supported")
    except UploadedFileNotFoundError:
        raise HTTPException(status_code=400, detail="File upload was not completed")
    except FileMetadataMismatchError:
        raise HTTPException(status_code=409, detail="Uploaded file metadata mismatch")



@router.get("/document/{document_id}", status_code=200, response_class=StreamingResponse,
            responses={200: {"description": "Binary stream"}})
async def download_document(document_id: int, user: User = Depends(get_current_user),
                            async_session: AsyncSession = Depends(get_session)) -> StreamingResponse:
    try:
        body, doc = await get_document(async_session, document_id, user.id)
        return StreamingResponse(
            body,
            media_type=doc.content_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(doc.filename)}"})
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the corresponding project")


@router.delete("/document/{document_id}", status_code=204)
async def delete_document(document_id: int, user: User = Depends(get_current_user),
                          async_session: AsyncSession = Depends(get_session)):
    try:
        await del_document(async_session, document_id, user.id)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the corresponding project")
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")


@router.put("/document/{document_id}", status_code=200, response_model=UpdateResponse)
async def update_document_request(document_id: int, request: UpdateRequest, user: User = Depends(get_current_user),
                                  async_session: AsyncSession = Depends(get_session)) -> UpdateResponse:
    try:
        return await prepare_for_update(async_session, document_id, user.id, request.content_type)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the corresponding project")
    except UnsupportedFileTypeError:
        raise HTTPException(status_code=415, detail="File type not supported")


@router.put("/document/{document_id}/complete", response_model=DocResponse, status_code=200)
async def update_document(document_id: int, request: FileRequest, user: User = Depends(get_current_user),
                          async_session: AsyncSession = Depends(get_session)) -> DocResponse:
    try:
        return await put_document(async_session, document_id, user.id, request)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the corresponding project")
    except UnsupportedFileTypeError:
        raise HTTPException(status_code=415, detail="File type not supported")
    except FileMetadataMismatchError:
        raise HTTPException(status_code=409, detail="Updated file metadata mismatch")
