from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView, ListView

import sys

if '/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house' not in sys.path:
    sys.path.append('/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house')


from house import USHouse

house = USHouse()


class IndexView(ListView):
    template_name = 'reps/index.html'
    context_object_name = 'rep_list'

    def get_queryset(self):
        reps = set(house._reps)

        active = self.request.GET.get('active')
        if active:
            reps &= house.search('reps', 'active', bool(active))
        else:
            reps &= house.search('reps', 'active', True)

        name = self.request.GET.get('name')
        if name:
            reps &= house.search('reps', 'name', name)

        chamber = self.request.GET.get('chamberOpt')
        if chamber and chamber != 'Both':
            reps &= house.search('reps', 'chamber', chamber)

        return reps


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


