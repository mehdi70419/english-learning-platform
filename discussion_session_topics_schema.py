from pydantic import BaseModel,ConfigDict
from datetime import datetime
from discussion_topic_schema import PublicDiscussionTopic



class CreateDiscussionSessionTopic(BaseModel):
    discussion_topic_id: int

class CreateDiscussionSessionTopicALLTogether(BaseModel):
    options:list[CreateDiscussionSessionTopic]


class PublicDiscussionSessionOfferedTopics(BaseModel):
        id: int
        chosen_topic_id: int | None
        scheduled_start_at: datetime
        scheduled_end_at: datetime
        actual_started_at: datetime | None
        actual_ended_at: datetime | None
        status: str
        participant_limit: int
        voting_closes_at: datetime
        registration_closes_at: datetime
        offered_topics: list[PublicDiscussionTopic]

        model_config = ConfigDict(from_attributes=True)