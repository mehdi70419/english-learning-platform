from pydantic import BaseModel



class PublicLessonProgress(BaseModel):

    sections_coverage_percentage:float
    number_of_completed_study_sessions:int