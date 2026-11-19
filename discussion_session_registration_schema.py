from pydantic import BaseModel,ConfigDict
from datetime import datetime

class PublicDiscussionSessionRegistration(BaseModel):
    id: int
    discussion_session_id: int
    user_id: int
    registered_at : datetime
    status: str
    cancelled_at : datetime  | None = None

    model_config = ConfigDict(from_attributes=True)
