from pydantic import BaseModel
from datetime import date



class PublicChartQuizPerformanceRecord(BaseModel):
    number_of_all_answers: int
    number_of_correct_answers: int
    number_of_incorrect_answers: int
    accuracy_percentage: float | None
    date: date

