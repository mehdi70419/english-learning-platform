from pydantic import BaseModel,ConfigDict
from datetime import datetime

from section_schema import PublicSection


class PublicStudySessionStart(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    started_at: datetime
    status:str
    last_activity_at: datetime
    section : PublicSection | None

    model_config=ConfigDict(from_attributes=True)



class PublicStudySessionEnd(BaseModel):
    id: int
    lesson_id: int
    user_id: int
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: float| None 
    last_activity_at: datetime
    status : str
    section : PublicSection | None

    model_config = ConfigDict(from_attributes=True)
