from .settings import *

# Use SQLite for local testing (no PostgreSQL needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Dummy keys for testing
GROQ_API_KEY = 'test-key'
SECRET_KEY = 'test-secret-key'
DEBUG = True


# Use dummy cache for tests (no Redis needed)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}