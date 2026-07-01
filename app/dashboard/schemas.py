from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class APIModel(BaseModel):
    @field_serializer("*", when_used="json")
    def serialize_datetime(self, value):
        if isinstance(value, datetime):
            return (
                value.replace(tzinfo=timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
        return value


class UserRegister(APIModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)
    repeat_password: str = Field(min_length=1)


class UserLogin(APIModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UserResponse(APIModel):
    user_id: int
    login: str
    created_at: datetime


class ProjectCreate(APIModel):
    name: str = Field(min_length=1)
    description: str | None = None


class ProjectResponse(APIModel):
    project_id: int
    name: str
    created_at: datetime
    owner_id: int


class ProjectUpdate(APIModel):
    name: str | None = None
    description: str | None = None


class DocResponse(APIModel):
    document_id: int
    filename: str
    size: int
    uploaded_at: datetime


class ProjectInfo(APIModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    project_id: int = Field(validation_alias="id")
    name: str
    description: str
    created_at: datetime
    owner_id: int


class UserProjects(APIModel):
    projects: list[ProjectInfo]

class ProjectInvite(APIModel):
    login: str = Field(min_length=1)
