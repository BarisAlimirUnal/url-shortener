# tests/test_routes.py
import pytest
import os


# Set test environment variables BEFORE importing the app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['UPSTASH_REDIS_REST_URL'] = 'https://fake-url.upstash.io'
os.environ['UPSTASH_REDIS_REST_TOKEN'] = 'fake-token'
os.environ['BASE_URL'] = 'http://localhost:5000'
os.environ['ENVIRONMENT'] = 'test'
os.environ['SECRET_KEY'] = 'test-secret-key'

from unittest.mock import patch, MagicMock
from app import create_app, db as _db
from app.models import URL


@pytest.fixture(scope='session')
def app():
    """Create a test app with an in-memory SQLite database"""
    test_app = create_app()
    test_app.config['TESTING'] = True
    test_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with test_app.app_context():
        _db.create_all()
        yield test_app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Clear the database between each test"""
    with app.app_context():
        _db.session.query(URL).delete()
        _db.session.commit()
    yield


# ---- Health Check ----

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'


# ---- Shorten URL ----

@patch('app.routes.cache_set')
def test_shorten_url_success(mock_cache, client):
    response = client.post('/shorten',
        json={'url': 'https://example.com'})
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data
    assert data['long_url'] == 'https://example.com'


def test_shorten_missing_url(client):
    response = client.post('/shorten', json={})
    assert response.status_code == 400


def test_shorten_invalid_url(client):
    response = client.post('/shorten', json={'url': 'not-a-valid-url'})
    assert response.status_code == 400


# ---- Redirect ----

@patch('app.routes.cache_set')
@patch('app.routes.cache_get')
def test_redirect_cache_hit(mock_cache_get, mock_cache_set, client, app):
    """When URL is in cache, database should NOT be called"""
    mock_cache_get.return_value = 'https://example.com'

    # Create a record in DB so click_count update works
    with app.app_context():
        url = URL(short_code='abc123', long_url='https://example.com', click_count=0)
        _db.session.add(url)
        _db.session.commit()

    response = client.get('/abc123')
    assert response.status_code == 302


@patch('app.routes.cache_set')
@patch('app.routes.cache_get')
def test_redirect_cache_miss(mock_cache_get, mock_cache_set, client, app):
    """When URL is not in cache, should fall back to DB"""
    mock_cache_get.return_value = None

    with app.app_context():
        url = URL(short_code='xyz789', long_url='https://example.com', click_count=0)
        _db.session.add(url)
        _db.session.commit()

    response = client.get('/xyz789')
    assert response.status_code == 302


@patch('app.routes.cache_get')
def test_redirect_not_found(mock_cache_get, client):
    mock_cache_get.return_value = None
    response = client.get('/doesnotexist')
    assert response.status_code == 404


# ---- Stats ----

@patch('app.routes.cache_set')
def test_stats_success(mock_cache, client, app):
    with app.app_context():
        url = URL(short_code='stat01', long_url='https://example.com', click_count=5)
        _db.session.add(url)
        _db.session.commit()

    response = client.get('/stats/stat01')
    assert response.status_code == 200
    assert response.get_json()['click_count'] == 5


def test_stats_not_found(client):
    response = client.get('/stats/doesnotexist')
    assert response.status_code == 404


# ---- Click Count ----

@patch('app.routes.cache_set')
@patch('app.routes.cache_get')
def test_click_count_increments(mock_cache_get, mock_cache_set, client, app):
    """Each redirect should increment the click counter by 1"""
    mock_cache_get.return_value = None

    with app.app_context():
        url = URL(short_code='click1', long_url='https://example.com', click_count=0)
        _db.session.add(url)
        _db.session.commit()

    client.get('/click1')
    client.get('/click1')

    response = client.get('/stats/click1')
    assert response.get_json()['click_count'] == 2