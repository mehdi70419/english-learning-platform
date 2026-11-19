from pydantic import BaseModel,ConfigDict


class CreateQuestionAnswerOption(BaseModel):
    option_text: str
    is_correct: bool


class CreateQuestionAnswerOptionALLTogether(BaseModel):
    options: list[CreateQuestionAnswerOption]


class PublicAnswerOptionForAdmin(BaseModel):
    id: int
    option_text: str
    is_correct: bool
    question_id: int

    model_config = ConfigDict(from_attributes=True)



class PublicAnswerOptionForUser(BaseModel):
    id: int
    option_text: str

    model_config = ConfigDict(from_attributes=True)



