from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.exceptions import NoAccessError, ProjectNotFoundError, UnsupportedFileTypeError, \
    DocumentNotFoundError
from app.dashboard.schemas import DocsResponse, DocResponse
from app.dashboard.service.security import get_current_user
from app.dashboard.service.service_docs import add_documents, get_document, del_document, put_document

from app.database.db import get_session
from app.database.models import User

router = APIRouter(tags=["documents"])


@router.post("/project/{project_id}/documents", response_model=DocsResponse, status_code=201)
async def upload_documents(project_id: int, files: list[UploadFile] = File(...), user: User = Depends(get_current_user),
                           async_session: AsyncSession = Depends(get_session)) -> DocsResponse:
    try:
        return await add_documents(async_session, project_id, user.id, files)
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the project")
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except UnsupportedFileTypeError:
        raise HTTPException(status_code=415, detail="File type not supported")


@router.get("/document/{document_id}", status_code=200, response_class=StreamingResponse,
            responses={200: {"description": "Binary stream"}})
async def download_document(document_id: int, user: User = Depends(get_current_user),
                            async_session: AsyncSession = Depends(get_session)) -> StreamingResponse:
    try:
        body, doc = await get_document(async_session, document_id, user.id)
        return StreamingResponse(
            body,
            media_type=doc.content_type,
            headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'})
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


@router.put("/document/{document_id}", status_code=200, response_model=DocResponse)
async def update_document(document_id: int, file: UploadFile = File(...), user: User = Depends(get_current_user),
                          async_session: AsyncSession = Depends(get_session)) -> DocResponse:
    try:
        return await put_document(async_session, document_id, user.id, file)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except NoAccessError:
        raise HTTPException(status_code=403, detail="User has no access to the corresponding project")
    except UnsupportedFileTypeError:
        raise HTTPException(status_code=415, detail="File type not supported")
