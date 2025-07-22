from django.http import HttpResponse
from court_database.models import Court

def index(request):
    courts = Court.objects.all()
    return HttpResponse(f'Hello World! We have {len(courts)} courts.')