from django.views.generic import ListView, DetailView

from court_database.models import Court, States, CourtType


class CourtListView(ListView):
    template_name = "ai_usage/court-list.html"
    paginate_by = 20
    model = Court

    def get_queryset(self):
        object_list = self.model.objects.all()

        if name := self.request.GET.get('name'):
            object_list = self.model.objects.filter(name__icontains=name)
        if court_state := self.request.GET.get('court_state'):
            if court_state != '-':
                object_list = object_list.filter(address__state=court_state)
        if court_type := self.request.GET.get('court_type'):
            if court_type != '-':
                object_list = object_list.filter(type=CourtType.objects.get(id=court_type))
        if ai_information := self.request.GET.get('ai_information'):
            if ai_information == 'True':
                object_list = object_list.filter(aifeedback__isnull=False).distinct()
            elif ai_information == 'False':
                object_list = object_list.filter(aifeedback__isnull=True).distinct()
        else:
            object_list = object_list.filter(aifeedback__isnull=False).distinct()

        return object_list.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Verwendung von KI an deutschen Gerichten | Seite {context['page_obj'].number}"
        context["states"] = States.choices
        context["court_types"] = CourtType.objects.all()
        return context


class CourtDetailView(DetailView):
    template_name = "ai_usage/court-detail.html"
    model = Court
    context_object_name = "court"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"KI Nutzung am {context['court']}"
        context["meta_description"] = (f"Informieren Sie sich über die Nutzung von KI am "
                                       f"{context['court']}.")
        context["meta_keywords"] = context["court"]
        return context