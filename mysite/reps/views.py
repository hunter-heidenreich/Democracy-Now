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

        party = self.request.GET.get('party')
        if party and party != 'All':
            reps &= house.search('reps', 'party', party)

        state = self.request.GET.get('state')
        if state and state != 'All':
            reps &= house.search('reps', 'state', state)

        return reps


def view(request, name):
    template = loader.get_template('reps/view.html')
    rep = list(house.search('reps', 'name', name))
    if rep:
        rep = rep[0]
        bills = house.search('reps', 'sponsor', rep.sources['url'])
        bills &= house.search('bills', 'congress', 116)
        bills = sorted(bills,
                       key=lambda bill: bill.get_overview()['sponsor']['date'],
                       reverse=True)
        print(bills)
        context = {
            'rep': rep,
            'bills': bills,
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse(template.render({}, request))


