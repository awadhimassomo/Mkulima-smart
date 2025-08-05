from decouple import config

DJANGO_ENV = config('DJANGO_ENV', default='dev').lower()

DEBUG = config('DEBUG', default=False, cast=bool)

if DJANGO_ENV == 'prod':
    if not DEBUG:
        from .productionSettings import *
        print("⚙️  Running in PRODUCTION mode with DEBUG =", DEBUG)
    else:
        raise RuntimeError("Production settings require DEBUG=False. Refusing to run with DEBUG=True in production.")
elif DJANGO_ENV == 'dev':
    if DEBUG:
        from .developmentSettings import *
        print("⚙️  Running in DEVELOPMENT mode with DEBUG =", DEBUG)
    else:
        raise RuntimeError("Development settings require DEBUG=True. Refusing to run with DEBUG=False in development.")
else:
    raise ValueError(f"Invalid DJANGO_ENV value: {DJANGO_ENV}. Use 'dev' or 'prod'.")
