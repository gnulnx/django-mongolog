=====
MongoLog
=====

MongoLog is a simple mongo based log handler that can be used easly used
with standard python/django logging

Quick start
-----------

1. Add "polls" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'mongolog',
    )

2. Add the MongoLoggerHandler to your LOGGING config::

    LOGGING = {
        'handler': {
            'mongologger': {
            'level': 'WARN',
            'class': 'mongolog.MongoLoggerHandler',
            'connection': 'mongodb://localhost:27017/'
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'mongologger'],
                'level': 'DEBUG',
                'propagate': True
            },
        },
    }

