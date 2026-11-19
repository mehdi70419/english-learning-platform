from pydantic import BaseModel
from datetime import date



class PublicChartStudyTimeRecord(BaseModel):
    date: date
    study_time : int
    hour : int | None = None

