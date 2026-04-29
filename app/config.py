# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL')
    UPSTASH_REDIS_REST_URL = os.getenv('UPSTASH_REDIS_REST_URL')    # changed
    UPSTASH_REDIS_REST_TOKEN = os.getenv('UPSTASH_REDIS_REST_TOKEN') # changed
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def validate(cls):
        required = ['DATABASE_URL', 'UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'BASE_URL']
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {missing}")