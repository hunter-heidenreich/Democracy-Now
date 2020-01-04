from django.shortcuts import render
from django.views.generic import TemplateView, ListView

# Create your views here.

import sys

if '/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house' not in sys.path:
    sys.path.append('/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house')


from house import HOUSE


class IndexView(ListView):
    template_name = 'bills/index.html'
    context_object_name = 'bills'

    def get_queryset(self):
        return HOUSE._bills
