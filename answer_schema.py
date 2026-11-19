from pydantic import BaseModel,ConfigDict
from datetime import datetime

class CreateAnswer(BaseModel):
    selected_answer: str 



class PublicAnswer(BaseModel):
    id: int
    question_id: int
    selected_answer: str
    user_id:int
    correctness:bool
    created_at: datetime
    correct_answer_snapshot:str



    model_config = ConfigDict(from_attributes=True)



