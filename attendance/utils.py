from django.conf import settings
from django.utils import timezone
from datetime import datetime

def get_current_date():
    """Get current date, or fake date if in development mode"""
    if settings.USE_FAKE_DATE:
        return datetime.strptime(settings.FAKE_DATE, "%Y-%m-%d").date()
    return timezone.now().date()

def get_current_datetime():
    """Get current datetime, or fake datetime if in development mode"""
    if settings.USE_FAKE_DATE:
        return timezone.make_aware(datetime.strptime(settings.FAKE_DATE, "%Y-%m-%d"))
    return timezone.now()