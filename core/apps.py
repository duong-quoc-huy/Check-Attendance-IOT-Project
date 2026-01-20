from django.apps import AppConfig
from django.utils import timezone
from datetime import datetime
import pytz

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        FAKE_TIME = datetime(
            2026, 1, 12, 7, 0, 0,
            tzinfo=pytz.timezone("Asia/Ho_Chi_Minh")
        )

        timezone.now = lambda: FAKE_TIME
