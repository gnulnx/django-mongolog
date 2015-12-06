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

    One of the cool things about mongolog is that it can log complex data structures
    in a way that makes them both human parsable and queryable.  So for instance if 
    we create a the following log message:

    .. code:: python

        
        # Pro Tip: You can copy and paste all of this
        
        LOG_MSG = {
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
                    ]
                } 
            }
        }

    Now let's log our message at each of the defined log levels...

    .. code:: python

        logger.debug(LOG_MSG)
        logger.info(LOG_MSG)
        logger.warn(LOG_MSG)
        logger.error(LOG_MSG)
        try:
            raise ValueError("Bad Value")
        except ValueError as e:
            logger.exception(LOG_MSG)

5) Now log into your mongo shell and look at some results
    
    .. code:: python
        
        db.mongolog.find({'level': "INFO"}).pretty()
        {
            "_id" : ObjectId("5664a22bdd162ca58f0693d2"),
            "name" : "__builtin__",
            "thread" : NumberLong("140735229362944"),
            
        }

