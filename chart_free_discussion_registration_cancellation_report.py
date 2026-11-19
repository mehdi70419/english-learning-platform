from pydantic import BaseModel
from datetime import date


class PublicChartFreeDiscussionRegistrationCancellationReport(BaseModel):
    number_of_all_registration_cancellation_activities: int
    number_of_registration_activity: int
    number_of_cancellation_activity: int
    date: date

    