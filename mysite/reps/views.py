from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.generic import TemplateView, ListView

from collections import Counter

import sys

if '/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house' not in sys.path:
    sys.path.append('/Users/hunterheidenreich/git/democracy-now/tools/us/federal/house')

from house import HOUSE


class IndexView(ListView):
    template_name = 'reps/index.html'
    context_object_name = 'rep_list'

    def get_queryset(self):
        reps = set(HOUSE._reps)

        active = self.request.GET.get('active')
        if active:
            reps &= HOUSE.search('reps', 'active', bool(active))
        else:
            reps &= HOUSE.search('reps', 'active', True)

        name = self.request.GET.get('name')
        if name:
            reps &= HOUSE.search('reps', 'name', name)

        chamber = self.request.GET.get('chamberOpt')
        if chamber and chamber != 'Both':
            reps &= HOUSE.search('reps', 'chamber', chamber)

        party = self.request.GET.get('party')
        if party and party != 'All':
            reps &= HOUSE.search('reps', 'party', party)

        state = self.request.GET.get('state')
        if state and state != 'All':
            reps &= HOUSE.search('reps', 'state', state)

        return reps


def view(request, name):
    template = loader.get_template('reps/view.html')
    rep = list(HOUSE.search('reps', 'name', name))
    if rep:
        rep = rep[0]

        sponsor = HOUSE.search('reps', 'sponsor', rep.sources['url'])
        sponsor &= HOUSE.search('bills', 'congress', 116)
        sponsor = sorted(sponsor,
                         key=lambda bill: bill.get_overview()['sponsor']['date'],
                         reverse=True)

        cosponsor = HOUSE.search('reps', 'cosponsor', rep.sources['url'])
        cosponsor &= HOUSE.search('bills', 'congress', 116)
        cosponsor = sorted(cosponsor,
                           key=lambda bill: bill.get_overview()['sponsor']['date'],
                           reverse=True)

        context = {
            'rep': rep,
            'sponsor': sponsor,
            'cosponsor': cosponsor,
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse(template.render({}, request))


def count_data(request, name, data):
    rep = list(HOUSE.search('reps', 'name', name))
    res = {}
    if rep:
        rep = rep[0]
        if data == 'sponsor_subj':
            sponsor = HOUSE.search('reps', 'sponsor', rep.sources['url'])
            cnt = Counter([bill.subjects['main']['title'] for bill in sponsor if 'main' in bill.subjects])
            cnt = sorted([{'label': k, 'value': v} for k, v in cnt.items()],
                         key=lambda x: x['value'], reverse=True)
            res['res'] = cnt
        elif data == 'cosponsor_subj':
            cosp = HOUSE.search('reps', 'cosponsor', rep.sources['url'])
            cnt = Counter([bill.subjects['main']['title'] for bill in cosp if 'main' in bill.subjects])
            cnt = sorted([{'label': k, 'value': v} for k, v in cnt.items()],
                         key=lambda x: x['value'], reverse=True)
            res['res'] = cnt

    return JsonResponse(res)

