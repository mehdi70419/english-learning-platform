from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CreateDiscussionSession(BaseModel):
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    participant_limit: int
    voting_closes_at: datetime
    registration_closes_at: datetime


class UpdateDiscussionSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheduled_start_at: datetime | None =None
    scheduled_end_at: datetime | None =None
    participant_limit: int | None =None
    voting_closes_at: datetime | None =None
    registration_closes_at: datetime | None =None
    chosen_topic_id: int | None =None


class PublicDiscussionSession(BaseModel):
    id: int
    chosen_topic_id: int  | None
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    actual_started_at: datetime  | None
    actual_ended_at: datetime  | None
    status: str
    participant_limit: int
    voting_closes_at: datetime
    registration_closes_at: datetime

    model_config = ConfigDict(from_attributes=True)


