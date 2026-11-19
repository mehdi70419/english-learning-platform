from pydantic import BaseModel


class PublicTotallStudyTime(BaseModel):
    total_study_time: str


class PublicStudyTimeReport(BaseModel):
    daily_study_time_report: str
    weekly_study_time_report: str
    monthly_study_time_report: str
    six_month_study_time_report: str
    yearly_study_time_report: str