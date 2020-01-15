from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views.generic import TemplateView


class CoreIndex(TemplateView):
    template_name = 'demviz/index.html'


def index(request):
    return HttpResponse("Hello, world. You're at the index.")