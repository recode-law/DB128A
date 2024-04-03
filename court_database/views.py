from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView
from django.http.response import HttpResponseRedirect

from helper.helper import is_member
from .forms import DetailedFeedbackForm
from .models import Court, Feedback, States, CourtType, RejectionReason


class CourtListView(ListView):
    template_name = "court_database/court-list.html"
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
                object_list = object_list.filter(type=court_type)
        if online_service_possible := self.request.GET.get('online_service_possible'):
            if online_service_possible == 'True':
                object_list = object_list.filter(online_service_possible_attr=True)
            elif online_service_possible == 'False':
                object_list = object_list.filter(online_service_possible_attr=False)
        if provides_online_service := self.request.GET.get('provides_online_service'):
            if provides_online_service == 'True':
                object_list = object_list.filter(provides_online_service_attr=True)
            elif provides_online_service == 'False':
                object_list = object_list.filter(provides_online_service_attr=False)

        return object_list.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Videoverhandlungen an deutschen Gerichten | Seite {context['page_obj'].number}"
        context["states"] = States.choices
        #context["court_types"] = CourtType.choices
        return context


class CourtDetailView(DetailView):
    template_name = "court_database/court-detail.html"
    model = Court
    context_object_name = "court"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reasons"] = [(reason.id, reason.name) for reason in RejectionReason.objects.all()]
        context["title"] = f"Videoverhandlungen am {context['court']}"
        context["meta_description"] = (f"Informieren Sie sich über die Möglichkeiten von Videoverhandlungen am "
                                       f"{context['court']}.")
        context["meta_keywords"] = context["court"]
        return context


def submit_positive_feedback(request, court_id):
    court = Court.objects.get(pk=court_id)
    feedback = Feedback()
    feedback.court = court
    feedback.provides_online_service = True

    quality = request.POST.get('quality', None)
    if quality is not None:
        feedback.online_service_quality = int(quality)

    feedback.creator_ip = request.META.get('REMOTE_ADDR')
    feedback.save()
    court.update_feedback_buffers()
    return HttpResponseRedirect(reverse("court-database-court-detail", args=[court_id]))


def submit_negative_feedback(request, court_id):
    court = Court.objects.get(pk=court_id)
    feedback = Feedback()
    feedback.court = court
    feedback.provides_online_service = False

    reason_id = request.POST.get('reason', None)
    if reason_id == 'other':
        feedback.other_rejection_reason = request.POST.get('otherReason', None)
    else:
        rejection_reason = RejectionReason.objects.get(id=reason_id)
        feedback.rejection_reason = rejection_reason

    feedback.creator_ip = request.META.get('REMOTE_ADDR')
    feedback.save()
    court.update_feedback_buffers()
    return HttpResponseRedirect(reverse("court-database-court-detail", args=[court_id]))


class CreateDetailedFeedbackFormView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    template_name = "court_database/court-feedback.html"
    form_class = DetailedFeedbackForm
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
