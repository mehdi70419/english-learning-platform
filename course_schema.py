from pydantic import BaseModel,ConfigDict
from datetime import datetime
from user_schema import PublicUser



class CreateCourse(BaseModel):
    title: str
    description: str
    level: str

class PublicCourse(BaseModel):
    id: int
    title: str
    description: str | None
    level: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateCourse(BaseModel):
    title: str | None =None
    description: str | None =None
    level: str | None =None


class PublicCourseUsers(BaseModel):
    id: int
    title: str
    description: str | None
    level: str
    created_at: datetime
    users:list[PublicUser]

    model_config = ConfigDict(from_attributes=True)
