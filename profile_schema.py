from pydantic import BaseModel,ConfigDict

class CreateProfile(BaseModel):
    first_name: str
    last_name: str
    bio:str | None =None
    avatar_url:str | None =None
    native_language:str | None =None
    learning_level:str | None =None

class PublicProfile(BaseModel):
    id: int
    first_name: str
    last_name: str
    bio: str | None
    avatar_url: str | None
    native_language: str | None
    learning_level: str | None
    user_id: int

    model_config = ConfigDict(from_attributes=True)