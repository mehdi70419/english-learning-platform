from pydantic import BaseModel,ConfigDict

class CreateVocabulary(BaseModel):
    word:str
    definition:str
    example_sentence:str
    part_of_speech:str
    pronunciation:str | None = None
    translation:str | None = None
    difficulty:str | None = None

class PublicVocabulary(BaseModel):
    id:int
    word:str
    definition:str
    example_sentence:str
    part_of_speech:str
    pronunciation:str | None
    translation:str | None
    difficulty:str | None
    lesson_id:int

    model_config = ConfigDict(from_attributes=True)


class UpdateVocabulary(BaseModel):
    word:str | None =None
    definition:str | None =None
    example_sentence:str | None =None
    part_of_speech:str | None =None
    pronunciation:str | None =None
    translation:str | None =None
    difficulty:str | None =None
