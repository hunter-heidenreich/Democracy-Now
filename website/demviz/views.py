from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView


class CoreIndex(TemplateView):
    template_name = 'demviz/index.html'


class QueryResult(ListView):
    template_name = 'demviz/queryres.html'
    context_object_name = 'results'

    def __init__(self):
        self.cls = None
        ListView.__init__(self)

    def get(self, request, *args, **kwargs):
        if 'cls' in kwargs:
            self.cls = kwargs['cls']

        self.object_list = self.get_queryset()

        context = self.get_context_data()
        return self.render_to_response(context)

    def get_queryset(self):
        if self.cls == 'reps':
            return []
        elif self.cls == 'bills':
            return []
        return []
