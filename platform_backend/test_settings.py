
from . import settings as base_settings

# Load the main Django settings without using wildcard imports
for name in dir(base_settings):
    if name.isupper():
        globals()[name] = getattr(base_settings, name)

del name
del base_settings

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
