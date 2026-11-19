from datetime import datetime
from pydantic import BaseModel,ConfigDict
from exercise_schema import PublicExercise2



class PublicQuestion2(BaseModel):
    id: int
    question_text: str
    question_type: str
    order: int
    points: int
    created_at: datetime
    exercise:PublicExercise2

    model_config = ConfigDict(from_attributes=True)