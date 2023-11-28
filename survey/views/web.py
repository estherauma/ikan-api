from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from survey.models import Survey


class SurveyView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'surveys.html')
    
class SurveyDataView(LoginRequiredMixin, View):
    def get(self, request):
        surveys = Survey.objects.all()
        item_list = []
        for item in surveys:
            item_dict = {
                'id': item.id,
                'questionKey': item.question_key,
                'questionText': item.question_text,
                'questionResponse': item.question_response
            }
            item_list.append(item_dict)
        return JsonResponse({'data': item_list})