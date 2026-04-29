# app/cache.py
from upstash_redis import Redis
from app.config import Config
from app.logger import get_logger

logger = get_logger(__name__)


def get_cache():
    """
    Returns an Upstash Redis client using the REST API.
    Works over HTTPS so no SSL config needed.
    """
    return Redis(
        url=Config.UPSTASH_REDIS_REST_URL,
        token=Config.UPSTASH_REDIS_REST_TOKEN
    )


def cache_get(short_code):
    """Try to get a URL from cache. Returns None if not found or on error."""
    try:
        client = get_cache()
        value = client.get(f"url:{short_code}")
        if value:
            logger.info(f"Cache HIT for short_code={short_code}")
        else:
            logger.info(f"Cache MISS for short_code={short_code}")
        return value
    except Exception as e:
        logger.error(f"Cache get failed, falling back to DB: {e}")
        return None


def cache_set(short_code, long_url, ttl=3600):
    """Store a URL in cache with a 1 hour expiry."""
    try:
        client = get_cache()
        client.set(f"url:{short_code}", long_url, ex=ttl)
        logger.info(f"Cached short_code={short_code} TTL={ttl}s")
    except Exception as e:
        logger.error(f"Cache set failed: {e}")