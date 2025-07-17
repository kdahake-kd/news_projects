from celery import shared_task
from .models import KeywordSearch
from .utils import fetch_and_store_news
import logging
import time
from celery.schedules import crontab

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def refresh_all_keywords(self):
    try:
        keywords = KeywordSearch.objects.values_list('keyword', flat=True).distinct()
        for keyword in keywords:
            try:
                fetch_and_store_news(keyword)
            except Exception as e:
                logger.error(f"Failed to fetch/store news for keyword '{keyword}': {str(e)}")
    except Exception as e:
        logger.critical(f"Failed refresh_all_keywords task: {str(e)}")

# for testing the code
@shared_task
def test_celery_task():
    print("Task started")
    time.sleep(5)
    print("Task finished")
    return "Done"