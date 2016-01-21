"""
import logging
logger = logging.getLogger('')

from django.views.generic.base import TemplateView


class HomeView(TemplateView):
    template_name = "mongolog/home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)

        context.update({
            #'last_10': 
        })


        try:
            raise ValueError("ERROR MESSAGE2")
        except Exception:
            logger.exception({
                'HomeView Test': True,
                'stack trace?': "pleace?"
            })
            raise

        return context
"""
