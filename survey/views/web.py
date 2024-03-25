from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from survey.models import Survey
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from collections import Counter


class SurveyView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'surveys.html')


class SurveyDataView(LoginRequiredMixin, View):
    def get(self, request):
        query_set = Survey.objects.values('question_key', 'question_text').distinct()
        survey_qtns = []
        for item in query_set:
            action = '<a href="/surveys/' + str(item["question_key"]) + '" \
                    class="btn btn-primary btn-sm"><i class="mdi mdi-eye"></i> \
                        Click to view question responses</a>'
            obj = {
                'questionKey': item['question_key'],
                'questionText': item['question_text'],
                'action': action
            }
            survey_qtns.append(obj)
        return JsonResponse({'data': survey_qtns})


class QuestionResponseDetailView(LoginRequiredMixin, View):
    def get(self, request, question_key):
        query_set = Survey.objects.filter(question_key=question_key)

        data = []
        for item in query_set:
            obj = {
                'id': item.id,
                'questionKey': item.question_key,
                'questionText': item.question_text,
                'questionResponse': item.question_response
            }
            data.append(obj)

        response_count = Counter(item['questionResponse'] for item in data)
        labels = list(response_count.keys())
        values = list(response_count.values())
        title = data[0]['questionText'] if len(data) > 0 else 'No responses'
        chart = self.get_plot(values, labels, title)
        return render(request, 'question-response.html', {'chart': chart})

    def get_graph(self):
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        img_png = buffer.getvalue()
        graph = base64.b64encode(img_png)
        graph = graph.decode('utf-8')
        buffer.close()
        return graph

    def get_plot(self, values, labels, title='Survey Responses'):
        plt.switch_backend('AGG')
        plt.figure(figsize=(6, 6))
        plt.pie(values, labels=labels, autopct='%1.1f%%',
                startangle=140, wedgeprops={'edgecolor': 'white'})
        plt.axis('equal')
        plt.title(title, loc='center', wrap=True)
        plt.tight_layout()
        graph = self.get_graph()
        return graph
