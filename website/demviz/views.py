import re
import sys

from django.views.generic import TemplateView, ListView
from django.http import JsonResponse

if 'tools/' not in sys.path:
    sys.path.append('tools/')

from database.congress import query_db


class CoreIndex(TemplateView):
    template_name = 'demviz/index.html'


class QueryResult(ListView):
    template_name = 'demviz/queryres.html'

    def __init__(self):
        self.cls = None
        ListView.__init__(self)

    def get(self, request, *args, **kwargs):
        if 'cls' in kwargs:
            self.cls = kwargs['cls']

        self.object_list = self.get_queryset()

        context = self.get_context_data()
        context['cls'] = self.cls
        return self.render_to_response(context)

    def get_queryset(self):
        if self.cls == 'reps':
            addr = self.request.GET.get('addr')
            rep = self.request.GET.get('rep')
            if addr:
                match = re.match('^.*,\s(\w{2})\s(\d{5})$', addr)
                if match:
                    state = match.group(1)
                    zipcode = match.group(2)

                    return query_db('reps', {
                        'state': state,
                        'active': True
                    })
            elif rep:
                return query_db('reps', {
                    'name': rep,
                    'active': True
                })

            return []
        elif self.cls == 'bills':
            return query_db('bills', {})
        return []


def json_reply(request, name):

    if request.path.split('/')[1] == 'bill':
        congress, title = name.split(' - ')
        return JsonResponse(query_db('bills', {
            'title': title,
            'congress': int(congress)
        })[0].get_json())
    elif request.path.split('/')[1] == 'rep':
        return JsonResponse(query_db('reps', {
            'name': name
        })[0].get_json())
    import pdb
    pdb.set_trace()

    return JsonResponse({})
