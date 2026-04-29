# app/routes.py
from flask import Blueprint, request, jsonify, redirect
from app import db
from app.models import URL
from app.cache import cache_get, cache_set
from app.utils import generate_short_code
from app.config import Config
from app.logger import get_logger
from datetime import datetime, timezone

bp = Blueprint('main', __name__)
logger = get_logger(__name__)


@bp.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    Railway uses this to verify your app is running correctly.
    Returns the current environment (dev/prod).
    """
    return jsonify({
        'status': 'healthy',
        'environment': Config.ENVIRONMENT
    }), 200


@bp.route('/shorten', methods=['POST'])
def shorten():
    """
    Takes a long URL and returns a short code.

    How to call it:
        POST /shorten
        Body: {"url": "https://www.example.com"}

    What it returns:
        {
            "short_code": "aB3xZ9",
            "short_url": "https://your-app.railway.app/aB3xZ9",
            "long_url": "https://www.example.com",
            "created_at": "2024-01-01T00:00:00"
        }
    """
    data = request.get_json()

    # Make sure a URL was actually sent
    if not data or not data.get('url'):
        logger.error("Request missing URL field")
        return jsonify({'error': 'URL is required'}), 400

    long_url = data['url']

    # Make sure it's actually a URL
    if not long_url.startswith(('http://', 'https://')):
        return jsonify({
            'error': 'URL must start with http:// or https://'
        }), 400

    # Generate a unique short code
    # Keep trying until we get one that doesn't already exist
    short_code = generate_short_code()
    while URL.query.filter_by(short_code=short_code).first():
        short_code = generate_short_code()

    # Save to database
    new_url = URL(
        short_code=short_code,
        long_url=long_url,
        created_at=datetime.now(timezone.utc),
        click_count=0
    )
    db.session.add(new_url)
    db.session.commit()

    # Also cache it immediately so the first redirect is fast
    cache_set(short_code, long_url)

    short_url = f"{Config.BASE_URL}/{short_code}"
    logger.info(f"Created short_url={short_url}")

    return jsonify({
        'short_code': short_code,
        'short_url': short_url,
        'long_url': long_url,
        'created_at': new_url.created_at.isoformat()
    }), 201


@bp.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    """
    Redirects the user to the original long URL.

    Flow:
        1. Check Redis cache first (very fast)
        2. If not in cache, check PostgreSQL database
        3. If not in database, return 404
        4. Increment the click counter
        5. Redirect the user
    """
    # Step 1 — Try cache (fast path, skips database)
    long_url = cache_get(short_code)

    # Step 2 — Cache miss, check database
    if not long_url:
        url_record = URL.query.filter_by(short_code=short_code).first()

        if not url_record:
            logger.error(f"short_code={short_code} not found")
            return jsonify({'error': 'Short URL not found'}), 404

        long_url = url_record.long_url

        # Store in cache so next visit is faster
        cache_set(short_code, long_url)

    # Step 3 — Increment click count in database
    url_record = URL.query.filter_by(short_code=short_code).first()
    if url_record:
        url_record.click_count += 1
        db.session.commit()

    logger.info(f"Redirecting short_code={short_code} → {long_url}")

    # 302 = temporary redirect (browser doesn't cache it,
    # so every visit gets counted)
    return redirect(long_url, code=302)


@bp.route('/stats/<short_code>', methods=['GET'])
def stats(short_code):
    """
    Returns analytics data for a short URL.

    How to call it:
        GET /stats/aB3xZ9

    What it returns:
        {
            "short_code": "aB3xZ9",
            "long_url": "https://www.example.com",
            "click_count": 42,
            "created_at": "2024-01-01T00:00:00"
        }
    """
    url_record = URL.query.filter_by(short_code=short_code).first()

    if not url_record:
        return jsonify({'error': 'Short URL not found'}), 404

    return jsonify(url_record.to_dict()), 200