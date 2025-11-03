from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView

from ai_usage.forms import AIFeedbackForm
from ai_usage.models import AIUsageGroup
from court_database.models import Court, States, CourtType
from helper.helper import is_member


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
        if ai_usage_groups := self.request.GET.getlist('ai_usage_groups'):
            object_list = object_list.filter(aifeedback__usage_groups__id__in=ai_usage_groups).distinct()

        return object_list.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Verwendung von KI an deutschen Gerichten | Seite {context['page_obj'].number}"
        context["states"] = States.choices
        context["court_types"] = CourtType.objects.all()
        context["ai_usage_groups"] = AIUsageGroup.objects.all()
        context["selected_ai_usage_groups"] = self.request.GET.getlist('ai_usage_groups')
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


class CreateAIFeedbackFormView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    template_name = "ai_usage/court-feedback.html"
    form_class = AIFeedbackForm
    success_url = "/"

    def test_func(self):
        return is_member(self.request.user, "Verifiziert")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["court"] = Court.objects.get(pk=self.kwargs["court_id"])
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        response = super().form_valid(form)
        form.instance.court.update_detailed_feedback_buffers()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        court = Court.objects.get(pk=self.kwargs["court_id"])
        context["title"] = f"Detailiertes Feedback für {court.name}"
        return context
