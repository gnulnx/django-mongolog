MongoLog
========

MongoLog is a simple Mongo based log handler that can be easly used
with standard python/django logging

Quick start
----------- 

1. Add "mongolog" to your INSTALLED_APPS like this::

    INSTALLED_APPS = (
        ...
        'mongolog',
    )

2. Add the MongoLoggerHandler to your LOGGING config
    .. code:: python

        LOGGING = {
            'handler': {
                'mongolog': {
                    'level': 'WARN',
                    'class': 'mongolog.MongoLogHandler',
                    'connection': 'mongodb://localhost:27017/'
                },
            },
            'loggers': {
                'django': {
                    'handlers': ['console', 'mongolog'],
                    'level': 'DEBUG',
                    'propagate': True
                },
            },
        }

3) Start your management shell::

    ./manage.py shell

4) Create a couple of log entries::
    
    import logging
    logger = logging.getLogger(__name__)

    logger.debug("A debug message")
    logger.info("An info message")
    logger.warning("A warning message")
    logger.error("An error message")
    try:
        raise ValueError("Bad Value")
    except ValueError as e:
        logger.exception("An exception message")

5) Now log into your mongo shell::

    mongo
    > use mongolog
    > db.mongolog.find({}).sort({'time.utc': -1}).limit(3)

    If you setup your logger with level 'WARN' like the example then
    you should now see three log entries corresponding to the warning, 
    error, and exception log statements.  However, you will not see the 
    debug and info statements unless you adjust the mongolog handler level 
    down to 'DEBUG'.
