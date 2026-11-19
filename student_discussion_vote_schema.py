from pydantic import BaseModel, ConfigDict
from datetime import datetime

class PublicStudentDiscussionVote(BaseModel):
    id:int
    discussion_session_id: int
    discussion_topic_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)