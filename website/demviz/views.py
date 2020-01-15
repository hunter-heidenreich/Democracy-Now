from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView


class CoreIndex(TemplateView):
    template_name = 'demviz/index.html'


class QueryResult(ListView):
    template_name = 'demviz/queryres.html'
    context_object_name = 'results'

    def get_queryset(self):
        return []
