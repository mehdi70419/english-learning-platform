from pydantic import BaseModel,ConfigDict




class CreateFillInTheBlankAnswer(BaseModel):
    accepted_answer: str



class PublicFillInTheBlankForAdmin(BaseModel):
    id: int
    question_id: int
    accepted_answer: str


    model_config = ConfigDict(from_attributes=True)

