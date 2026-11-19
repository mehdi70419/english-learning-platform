from apscheduler.triggers import date
from pydantic import BaseModel,ConfigDict
from datetime import datetime


class CreateUser(BaseModel):
    username:str
    email:str
    password:str


class UpdateUser(BaseModel):
    username:str | None =None
    email:str | None =None


class PublicUser(BaseModel):
    id:int
    username:str
    email:str
    role:str
    created_at:datetime
    last_activity_at:datetime | None

    model_config = ConfigDict(from_attributes=True)





