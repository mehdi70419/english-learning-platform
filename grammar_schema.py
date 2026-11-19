from pydantic import BaseModel,ConfigDict


class CreateGrammar(BaseModel):
    title: str
    explanation: str
    examples: str | None =None
    order: int | None =None


class UpdateGrammar(BaseModel):
    title: str | None =None
    explanation: str | None =None
    examples: str | None =None
    order: int | None =None




class PublicGrammar(BaseModel):
    id: int
    title: str
    explanation: str
    examples: str | None
    order:  int | None
    lesson_id: int

    model_config = ConfigDict(from_attributes=True)





