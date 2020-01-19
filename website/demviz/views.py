import sys

from django.views.generic import TemplateView, ListView

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
        return self.render_to_response(context)

    def get_queryset(self):
        if self.cls == 'reps':
            addr = self.request.GET.get('addr')

            import pdb
            pdb.set_trace()
            return query_db('reps', {})
        elif self.cls == 'bills':
            return query_db('bills', {})
        return []
