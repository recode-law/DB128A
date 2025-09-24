from django.http import HttpResponse
from django.shortcuts import render

from court_database.models import Court

def index(request):
    courts = Court.objects.all()
    return render(request, 'subapp_test/test.html', {'courts': courts})