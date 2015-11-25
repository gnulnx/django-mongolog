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

3) Start you management shell::

    ./manage.py shell

4) Create a a couple of log entries::
    
    import logging
    logger = logging.getLogger(__name__)

    logger.debug("A debug message")
    logger.info("An info message")
    logger.warning("A Serious warning")
    logger.error("We have an ERROR")
    try:
        raise ValueError("Bad Value")
    except ValueError as e:
        logger.exception("This is the worste exception ever")

5) Now log into your mongo shell::

    mongo
    > use mongologger
    > db.mongologger.find().sort({created: -1}).limit(5).pretty()

    If you setup your logger with level 'WARN' like the example then
    you should now see three log entries corresponding to the warning, 
    error, and exception log statements.  However, you will not see the 
    debug and info statements unless you adjust the level down to 'DEBUG'.
