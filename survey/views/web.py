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
        query_set = Survey.objects.values('question_key', 'question_text').distinct()
        survey_qtns = []
        for item in query_set:
            print
            obj = {
                'questionKey': item['question_key'],
                'questionText': item['question_text'],
                'action': '<a href="/surveys/' + str(item['question_key']) + '" class="btn btn-primary btn-sm"><i class="mdi mdi-eye"></i> Click to view question responses</a>'
            }
            survey_qtns.append(obj)
        return JsonResponse({'data': survey_qtns})
