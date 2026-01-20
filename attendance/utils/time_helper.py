from django.utils import timezone
from django.conf import settings
from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time():
    """
    Get current time - returns fake time if FAKE_TIME is set in settings,
    otherwise returns real time
    """
    if hasattr(settings, 'FAKE_TIME_ENABLED') and settings.FAKE_TIME_ENABLED:
        if hasattr(settings, 'FAKE_TIME'):
            fake_dt = datetime.strptime(settings.FAKE_TIME, '%Y-%m-%d %H:%M:%S')
            fake_dt = fake_dt.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
            return fake_dt
    
    return timezone.now()