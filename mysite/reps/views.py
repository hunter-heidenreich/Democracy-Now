from django.http import HttpResponse
from django.template import loader

import sys

if '/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house' not in sys.path:
    sys.path.append('/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house')


from house import USHouse

house = USHouse()


def index(request):
    reps = house._reps
    template = loader.get_template('reps/index.html')
    context = {
        'rep_list': reps,
    }
    return HttpResponse(template.render(context, request))


def view(request, name):
    rep = house.search('reps', 'name', name).pop()
    template = loader.get_template('reps/view.html')
    context = {
        'rep': rep,
    }
    return HttpResponse(template.render(context, request))


