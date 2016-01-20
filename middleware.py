import logging
logger = logging.getLogger()

class RequestMiddleware(object):

    def __init__(self):
        """
        It makes me sad that ``auth.get_user`` can't be customized, but instead we
        have to monkeypatch it.
        """
        auth.get_user = cookie_get_user

    def process_request(self, request):
        logger.info(request.__dict__)

    def process_response(self, request, response):
        pass

