from pydantic import BaseModel,ConfigDict




class CreateSection(BaseModel):
    name:str



class PublicSection(BaseModel):
    id: int
    name: str
    lesson_id: int

    model_config = ConfigDict(from_attributes=True)


class CreateSection2(BaseModel):

    section_id: int | None =None



class UpdateSection(BaseModel):

    name: str | None =None


class UpdateSection2(BaseModel):

    name: str | None =None
    lesson_id: int




