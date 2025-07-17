from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')

app = Celery('news_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Celery Beat schedule
from celery.schedules import crontab

app.conf.beat_schedule = {
    'refresh-keywords-every-hour': {
        'task': 'news.tasks.refresh_all_keywords',
        'schedule': crontab(minute=0, hour='*/1'),  # every 1 hour
    },
}
