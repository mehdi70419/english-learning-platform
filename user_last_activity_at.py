from datetime import datetime,timezone
from user_model import User


def helper_function_update_user_last_activity(current_user:User):

    current_time = datetime.now(timezone.utc)

    current_user.last_activity_at = current_time
    return current_user.last_activity_at

