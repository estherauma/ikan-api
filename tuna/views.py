from django.http import HttpResponse
from decouple import config

enviroment = config('ENVIRONMENT', 'Development')
def welcome(request):
    return HttpResponse(f"Welcome to the Tuna {enviroment} API")
