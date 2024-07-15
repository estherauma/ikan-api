from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from survey.models import Survey, InlineQuestion
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from collections import Counter
from matplotlib.ticker import MaxNLocator
from textwrap import fill


class SurveyView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'is_tfa_video': False,
            'is_inline_question': False,
            'is_survey': False,
        }

        if request.path == '/surveys/tfa-video/':
            context['is_tfa_video'] = True
        elif request.path == '/surveys/inline-questions/':
            context['is_inline_question'] = True
        else:
            context['is_survey'] = True

        return render(request, 'surveys.html', context)


class SurveyDataView(LoginRequiredMixin, View):
    def get(self, request):
        query_set = Survey.objects.values('question_key', 'question_text')\
            .distinct().exclude(question_key__startswith='tfaVid')

        survey_qtns = []
        for item in query_set:
            action = f'<a\
                        href="/surveys/{str(item["question_key"])}" \
                        class="btn btn-primary btn-sm">\
                            <i class="mdi mdi-eye"></i> \
                            Click to view survey question responses\
                        </a>'
            obj = {
                'questionKey': item['question_key'],
                'questionText': item['question_text'],
                'action': action
            }
            survey_qtns.append(obj)

        return JsonResponse({'data': survey_qtns})


class TFAVideoDataView(LoginRequiredMixin, View):
    def get(self, request):
        query_set = Survey.objects.filter(question_key__startswith='tfaVid')\
            .values('question_key', 'question_text').distinct()

        tfa_video_qtns = []
        for item in query_set:
            action = f'<a\
                        href="/surveys/tfa-video/{str(item["question_key"])}" \
                        class="btn btn-primary btn-sm">\
                            <i class="mdi mdi-eye"></i> \
                            Click to view TFA video question responses\
                        </a>'
            obj = {
                'questionKey': item['question_key'],
                'questionText': item['question_text'],
                'action': action
            }
            tfa_video_qtns.append(obj)

        return JsonResponse({'data': tfa_video_qtns})


class InlineQuestionDataView(LoginRequiredMixin, View):
    def get(self, request):
        query_set = InlineQuestion.objects.values('question_key', 'question_text').distinct()

        inline_qtns = []
        for item in query_set:
            action = f'<a\
                        href="/surveys/inline-questions/{str(item["question_key"])}" \
                        class="btn btn-primary btn-sm">\
                            <i class="mdi mdi-eye"></i> \
                            Click to view inline question responses\
                        </a>'
            obj = {
                'questionKey': item['question_key'],
                'questionText': item['question_text'],
                'action': action
            }
            inline_qtns.append(obj)

        return JsonResponse({'data': inline_qtns})


class QuestionResponseDetailView(LoginRequiredMixin, View):
    def get(self, request, question_key):
        if 'surveys/inline-questions' in request.path:
            query_set = InlineQuestion.objects.filter(question_key=question_key)
        else:
            query_set = Survey.objects.filter(question_key=question_key)

        data = query_set.values()
        if len(data) > 0:
            question_type = data[0]['question_type']
            question_text = data[0]['question_text']
        else:
            question_type = None
            question_text = 'No responses'

        response_count = self.get_response_count(data, question_type)
        labels = list(response_count.keys())
        values = list(response_count.values())
        title = question_text

        if question_type in ['text', 'textArea', 'textarea']:
            table_data = sorted(response_count.items(), key=lambda item: item[1], reverse=True)
            return render(request, 'question-response.html', {'table_data': table_data, 'title': title})
        else:
            chart = self.get_plot(values, labels, title, question_type)
            return render(request, 'question-response.html', {'chart': chart, 'title': title})

    def get_response_count(self, data, question_type):
        if question_type in ['multiple-select', 'multi-select']:
            all_responses = []
            for item in data:
                all_responses.extend(item['question_response'].split(','))
            return Counter(all_responses)
        else:
            return Counter(item['question_response'] for item in data)

    def get_graph(self):
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        img_png = buffer.getvalue()
        graph = base64.b64encode(img_png)
        graph = graph.decode('utf-8')
        buffer.close()
        return graph

    def get_plot(self, values, labels, title, question_type):
        plt.switch_backend('AGG')
        plt.figure(figsize=(10, 6))
        
        wrapped_labels = [fill(label, width=25) for label in labels]

        if question_type == 'radio':
            wedges, texts, autotexts = plt.pie(values, labels=wrapped_labels, autopct='%1.1f%%', startangle=140, wedgeprops={'edgecolor': 'white'})
            plt.axis('equal')
            colors = [wedge.get_facecolor() for wedge in wedges]
            plt.legend(handles=wedges, labels=wrapped_labels, loc='lower left', frameon=False)
        elif question_type in ['select', 'multiple-select', 'multi-select']:
            bars = plt.barh(wrapped_labels, values, color='skyblue')
            plt.xlabel('Number of Responses')
            plt.ylabel('Responses')
            plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
            colors = [bar.get_facecolor() for bar in bars]
            plt.subplots_adjust(bottom=0.3)

            legend_wrapped_labels = [fill(label, width=40) for label in labels]
            legend_labels = [f"{label} ({value} responses)" for label, value in zip(legend_wrapped_labels, values)]
            plt.legend(handles=bars, labels=legend_labels, bbox_to_anchor=(-0.1, -0.2), loc='lower left', frameon=False)

        plt.title(title, loc='center', wrap=True)
        plt.tight_layout()
        graph = self.get_graph()
        return graph
