from pydantic import BaseModel, ConfigDict
from exercise_schema import PublicExercise
from vocabulary_schema import PublicVocabulary
from section_schema import PublicSection
from grammar_schema import PublicGrammar



class CreateLesson(BaseModel):
    title: str
    description: str
    content: str
    order: int

class PublicLesson(BaseModel):
    id: int
    title: str
    description: str
    content: str
    order: int
    course_id:int

    model_config = ConfigDict(from_attributes=True)


class UpdateLesson(BaseModel):
    title: str | None =None
    description: str | None =None
    content: str | None =None
    order: int | None =None