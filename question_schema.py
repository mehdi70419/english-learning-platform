from pydantic import BaseModel,ConfigDict
from datetime import datetime
from answer_option_schema import PublicAnswerOptionForUser


class CreateQuestion(BaseModel):
    question_text: str
    question_type: str
    order: int
    points:int

class PublicQuestion(BaseModel):
    id: int
    question_text: str
    question_type: str
    order: int
    points: int
    created_at: datetime
    answer_options:list[PublicAnswerOptionForUser]
    exercise_id: int

    model_config = ConfigDict(from_attributes=True)



class UpdateQuestion(BaseModel):
    question_text: str | None =None
    question_type: str | None =None
    order: int | None =None
    points: int | None =None




