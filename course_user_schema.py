from pydantic import BaseModel,ConfigDict



class PublicEnrollment(BaseModel):
    user_id: int
    course_id: int

    model_config = ConfigDict(from_attributes=True)


