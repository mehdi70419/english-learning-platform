from pydantic import BaseModel,ConfigDict
from datetime import datetime
from question_schema import PublicQuestion


class CreateExercise(BaseModel):
    title: str
    instructions: str
    exercise_type: str
    difficulty: str
    order:int



class PublicExercise(BaseModel):
    id: int
    title: str
    instructions: str
    exercise_type: str
    difficulty: str
    order: int
    created_at: datetime
    lesson_id: int

    model_config=ConfigDict(from_attributes=True)


class UpdateExercise(BaseModel):
    title: str | None =None
    instructions: str | None =None
    exercise_type: str | None =None
    difficulty: str | None =None
    order: int | None =None


class PublicExercise2(BaseModel):
    id: int
    title: str
    instructions: str
    exercise_type: str
    difficulty: str
    order: int
    created_at: datetime

    model_config=ConfigDict(from_attributes=True)