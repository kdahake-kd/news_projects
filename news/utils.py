import requests
from .models import NewsArticle
import logging

logger = logging.getLogger(__name__)

def fetch_and_store_news(keyword):
    try:
        api_key = 'c1988fa638df408f8c67c4543ae7d9c7'
        url = f'https://newsapi.org/v2/everything?q={keyword}&apiKey={api_key}'
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.warning(f"News API error for '{keyword}': {response.status_code} {response.text}")
            return

        data = response.json()
        articles = data.get('articles', [])

        for article in articles:
            try:
                NewsArticle.objects.update_or_create(
                    title=article['title'],
                    keyword=keyword,
                    defaults={
                        'description': article.get('description', ''),
                        'url': article.get('url'),
                        'published_at': article.get('publishedAt'),
                    }
                )
            except Exception as e:
                logger.error(f"DB save error for article '{article.get('title')}': {str(e)}")

    except Exception as e:
        logger.critical(f"Failed fetch/store for keyword '{keyword}': {str(e)}")
