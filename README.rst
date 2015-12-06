MongoLog 
========

MongoLog is a simple Mongo based log handler that can be easly used
with standard python/django logging.

 .. image:: https://coveralls.io/repos/gnulnx/django-mongolog/badge.svg?branch=master&service=github :target: https://coveralls.io/github/gnulnx/django-mongolog?branch=master

Quick start
----------- 

1. Add "mongolog" to your INSTALLED_APPS like this
    .. code:: python

        INSTALLED_APPS = (
            ...
            'mongolog',
        )

2. Add the SimpleMongoLoggerHandler to your LOGGING config.  
    .. code:: python

        LOGGING = {
            'version': 1,
            'handlers': {
                'mongolog': {
                    'level': 'DEBUG',
                    'class': 'mongolog.SimpleMongoLogHandler',
                    'connection': 'mongodb://localhost:27017'
                },
            },
            'loggers': {
                '': {
                    'handlers': ['mongolog'],
                    'level': 'DEBUG',
                    'propagate': True
                },
            },
        }

3) Start your management shell::

    ./manage.py shell

4) Create a couple of log entries
    .. code:: python
    
        import logging
        import pymongo
        logger = logging.getLogger(__name__)

        TEST_MSG = {
            'test': True,  
            'test class': 'TestBaseMongoLogHandler',
            'Life': {
                'Domain': {
                    'Bacteria': [
                        {
                            'name': ValueError,
                            'description': 'Just a bad description'
                        }
                    ],
                    'Archaea': [],
                    'Eukaryota': [
                        {
                            'name': 'Excavata', 
                            'description': 'Various flagellate protozoa',
                        },
                        {   
                            'name': 'Amoebozoa',
                            'descritpion': 'most lobose amoeboids and slime moulds',
                        },
                        {
                            'name': 'Opisthokonta',
                            'description': 'animals, fungi, choanoflagellates, etc.',
                        },
                        {
                            'name': 'Rhizaria',
                            'description': 'Foraminifera, Radiolaria, etc'
                        },
                        {   
                            'name': 'Chromalveolata',
                            'description': 'Stramenopiles (Brown Algae, Diatoms etc.)'
                        },
                        {
                            'name': 'Archaeplastida',
                            'description': 'Land plants, green algae, red algae, and glaucophytes'
                        },
                    ]
                } 
            }
        }

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
