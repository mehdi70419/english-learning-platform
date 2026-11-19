from pydantic import BaseModel,ConfigDict



class CreateDiscussionTopic(BaseModel):
    title: str
    description: str


class UpdateDiscussionTopic(BaseModel):
    title: str  | None =None
    description: str  | None =None
    is_active: bool  | None =None


class PublicDiscussionTopic(BaseModel):
    id: int
    title: str
    description: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
