import logging
logger = logging.getLogger("mongolog.request")


class RequestMiddleware(object):

    def process_request(self, request):
        logger.info(request.__dict__)
