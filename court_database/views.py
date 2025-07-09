import json

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.paginator import EmptyPage
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.views.decorators.http import require_http_methods
from django.http.response import HttpResponseRedirect
from django.db import IntegrityError

from helper.helper import is_member, group_required
from user_signup.authentication import basic_auth_required
from .forms import DetailedFeedbackForm
from .models import Court, Feedback, States, CourtType, RejectionReason, InvalidStateError
from .rest_api import (create_court, get_court_detail, get_court_ids, create_court_type, get_court_types, get_states,
                       get_rest_api_info, create_court_feedback, create_court_detailed_feedback,
                       create_camera_perspective, create_conferencing_software, get_camera_perspectives,
                       get_conferencing_software, get_rejection_reasons, CourtListLimitExceededError)


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
                object_list = object_list.filter(type=CourtType.objects.get(id=court_type))
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
        context["court_types"] = CourtType.objects.all()
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
    if request.method == 'POST':
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
    if request.method == 'POST':
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


class APIInfoView(TemplateView):
    template_name = "court_database/api-information.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["apis"] = get_rest_api_info(self.request.build_absolute_uri("/").rstrip("/"))
        return context


@csrf_exempt
@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["GET", "POST"])
def rest_api_court(request):
    if request.method == "GET":
        try:
            response_data = get_court_ids(request.GET)
        except ValueError:
            return HttpResponse(status=400, content="Invalid page or per_page parameter")
        except EmptyPage:
            return HttpResponse(status=404, content="The requested page is empty")
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    else:
        try:
            response_data = create_court(json.loads(request.body), request.user)
        except KeyError as e:
            return HttpResponse(status=400, content=f"Missing required field: {str(e)}")
        except Court.DoesNotExist:
            return HttpResponse(status=404, content="Parent court does not exist")
        except CourtType.DoesNotExist:
            return HttpResponse(status=404, content="Selected court type does not exist")
        except IntegrityError as e:
            return HttpResponse(status=400, content=f"Error creating court: {str(e)}")
        except InvalidStateError as e:
            return HttpResponse(status=404, content=f"Invalid state provided: {str(e)}")
        except json.JSONDecodeError:
            return HttpResponse(status=400, content="Invalid JSON format in request body")
        except ValueError as e:
            return HttpResponse(status=400, content=f"Invalid value provided: {str(e)}")
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(json.dumps(response_data), status=200 if request.method == "GET" else 201, content_type="application/json")


@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["GET"])
def rest_api_court_detail(request):
    try:
        response_data = get_court_detail(request.GET)
    except KeyError as e:
        return HttpResponse(status=400, content=f"Missing parameter: {str(e)}")
    except Court.DoesNotExist:
        return HttpResponse(status=404, content="One or more courts do not exist")
    except CourtListLimitExceededError as e:
        return HttpResponse(status=400, content=str(e))
    except ValueError:
        return HttpResponse(status=400, content="IDs must be integers")
    except Exception as e:
        return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@csrf_exempt
@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["GET", "POST"])
def rest_api_court_type(request):
    if request.method == "GET":
        try:
            response_data = get_court_types()
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    else:
        try:
            response_data = create_court_type(json.loads(request.body), request.user)
        except KeyError as e:
            return HttpResponse(status=400, content=f"Missing required field: {str(e)}")
        except IntegrityError as e:
            return HttpResponse(status=400, content=f"Error creating court type: {str(e)}")
        except json.JSONDecodeError:
            return HttpResponse(status=400, content="Invalid JSON format in request body")
        except ValueError as e:
            return HttpResponse(status=400, content=f"Invalid value provided: {str(e)}")
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(json.dumps(response_data), status=200 if request.method == "GET" else 201, content_type="application/json")


@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["GET"])
def rest_api_state(request):
    try:
        response_data = get_states()
    except Exception as e:
        return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@csrf_exempt
@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["POST"])
def rest_api_court_feedback(request):
    try:
        create_court_feedback(json.loads(request.body), request.user)
    except KeyError as e:
        return HttpResponse(status=400, content=f"Missing required field: {str(e)}")
    except IntegrityError as e:
        return HttpResponse(status=400, content=f"Error creating feedback: {str(e)}")
    except json.JSONDecodeError:
        return HttpResponse(status=400, content="Invalid JSON format in request body")
    except ValueError as e:
        return HttpResponse(status=400, content=f"Invalid value provided: {str(e)}")
    except RejectionReason.DoesNotExist:
        return HttpResponse(status=400, content="Selected rejection reason does not exist")
    except Court.DoesNotExist:
        return HttpResponse(status=404, content="Selected Court does not exist")
    except Exception as e:
        return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(status=201, content_type="text/plain")


@csrf_exempt
@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["POST"])
def rest_api_court_detailed_feedback(request):
    try:
        create_court_detailed_feedback(json.loads(request.body), request.user)
    except KeyError as e:
        return HttpResponse(status=400, content=f"Missing required field: {str(e)}")
    except IntegrityError as e:
        return HttpResponse(status=400, content=f"Error creating detailed feedback: {str(e)}")
    except json.JSONDecodeError:
        return HttpResponse(status=400, content="Invalid JSON format in request body")
    except ValueError as e:
        return HttpResponse(status=400, content=f"Invalid value provided: {str(e)}")
    except Court.DoesNotExist:
        return HttpResponse(status=404, content="Selected Court does not exist")
    except Exception as e:
        return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(status=201, content_type="text/plain")


@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["GET"])
def rest_api_rejection_reason(request):
    try:
        response_data = get_rejection_reasons()
    except Exception as e:
        return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(json.dumps(response_data), content_type="application/json")


@csrf_exempt
@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["GET", "POST"])
def rest_api_camera_perspective(request):
    if request.method == "GET":
        try:
            response_data = get_camera_perspectives()
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    else:
        try:
            response_data = create_camera_perspective(json.loads(request.body), request.user)
        except KeyError as e:
            return HttpResponse(status=400, content=f"Missing required field: {str(e)}")
        except IntegrityError as e:
            return HttpResponse(status=400, content=f"Error creating camera perspective: {str(e)}")
        except json.JSONDecodeError:
            return HttpResponse(status=400, content="Invalid JSON format in request body")
        except ValueError as e:
            return HttpResponse(status=400, content=f"Invalid value provided: {str(e)}")
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(json.dumps(response_data), status=200 if request.method == "GET" else 201, content_type="application/json")


@csrf_exempt
@basic_auth_required
@group_required("Verifiziert")
@require_http_methods(["GET", "POST"])
def rest_api_conferencing_software(request):
    if request.method == "GET":
        try:
            response_data = get_conferencing_software()
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    else:
        try:
            response_data = create_conferencing_software(json.loads(request.body), request.user)
        except KeyError as e:
            return HttpResponse(status=400, content=f"Missing required field: {str(e)}")
        except IntegrityError as e:
            return HttpResponse(status=400, content=f"Error creating conferencing software: {str(e)}")
        except json.JSONDecodeError:
            return HttpResponse(status=400, content="Invalid JSON format in request body")
        except ValueError as e:
            return HttpResponse(status=400, content=f"Invalid value provided: {str(e)}")
        except Exception as e:
            return HttpResponse(status=500, content=f"Internal server error: {str(e)}")
    return HttpResponse(json.dumps(response_data), status=200 if request.method == "GET" else 201, content_type="application/json")
