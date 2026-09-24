from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from survey.models import Survey, InlineQuestion
import base64
from io import BytesIO
from collections import Counter
from matplotlib.ticker import MaxNLocator
import matplotlib.cm as cm
import numpy as np
from textwrap import fill
from django.db.models import Q
from matplotlib.figure import Figure


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
        consent_qtn_key = 'i-have-read-and-understood-all-of-the-information-above-and-consent-to-have-my-de-\
            identified-data-from-ikan-used-as-part-of-the-research-study'
        query_set = Survey.objects.values('question_key', 'question_text')\
            .distinct().exclude(Q(question_key__startswith='tfaVid') | Q(question_key=consent_qtn_key))

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

        # get follow up question responses data
        follow_up_data = self.get_follow_up_qtn_responses(query_set)

        if question_type in ['text', 'textArea', 'textarea']:
            table_data = sorted(response_count.items(), key=lambda item: item[1], reverse=True)
            context = {
                'table_data': table_data,
                'title': title,
                'follow_up_data': follow_up_data if follow_up_data else None
            }
            return render(request, 'question-response.html', context)
        else:
            chart = self.get_plot(values, labels, title, question_type)
            context = {
                'chart': chart,
                'title': title,
                'follow_up_data': follow_up_data if follow_up_data else None
            }
            return render(request, 'question-response.html', context)

    def get_response_count(self, data, question_type, is_follow_up_response=False):
        if question_type in ['multiple-select', 'multi-select']:
            all_responses = []
            for item in data:
                if is_follow_up_response:
                    all_responses.extend(item['follow_up_question_response'].split(','))
                else:
                    all_responses.extend(item['question_response'].split(','))
            return Counter(all_responses)
        else:
            if is_follow_up_response:
                return Counter(item['follow_up_question_response'] for item in data)
            return Counter(item['question_response'] for item in data)

    def get_graph(self, fig):
        with BytesIO() as buffer:
            fig.savefig(buffer, format='png', bbox_inches='tight')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def get_plot(self, values, labels, title, question_type):
        # 1. Create an isolated Figure and Axes object directly
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(1, 1, 1)

        wrapped_labels = [fill(label, width=25) for label in labels]

        if question_type == 'radio':
            # ax.pie returns a tuple of (wedges, texts, autotexts)
            wedges, texts, autotexts = ax.pie(
                values,
                labels=wrapped_labels,
                autopct='%1.1f%%',
                startangle=140,
                wedgeprops={'edgecolor': 'white'}
            )
            ax.axis('equal')

            legend_labels = [
                f"{label} ({value} responses)"
                for label, value in zip(wrapped_labels, values)
            ]
            ax.legend(
                handles=wedges,
                labels=legend_labels,
                loc='lower left',
                frameon=False
            )

        elif question_type in ['select', 'multiple-select', 'multi-select']:
            colors = cm.tab20(np.linspace(0, 1, len(labels)))
            bars = ax.barh(wrapped_labels, values, color=colors)

            ax.set_xlabel('Number of Responses')
            ax.set_ylabel('Responses')
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            fig.subplots_adjust(bottom=0.3)

            legend_wrapped_labels = [fill(label, width=70) for label in labels]
            legend_labels = [
                f"{label} ({value} responses)"
                for label, value in zip(legend_wrapped_labels, values)
            ]
            ax.legend(
                handles=bars,
                labels=legend_labels,
                bbox_to_anchor=(-0.1, -0.3),
                loc='lower left',
                frameon=False
            )

        ax.set_title(title, loc='center', wrap=True)
        fig.tight_layout(rect=[0, 0.05, 1, 1])

        # Pass the fig object explicitly to get_graph()
        graph = self.get_graph(fig)

        # Clean up figure memory without invoking pyplot global state
        fig.clf()

        return graph

    def get_follow_up_qtn_responses(self, query_set):
        follow_up_qtns = query_set.filter(follow_up_question_key__isnull=False).values()
        unique_follow_up_qtns = query_set.filter(follow_up_question_key__isnull=False).values(
            'follow_up_question_key').distinct()

        follow_up_data = []
        for obj in unique_follow_up_qtns:
            follow_up_qtn = follow_up_qtns.filter(follow_up_question_key=obj['follow_up_question_key']).values()
            follow_up_question_type = follow_up_qtn[0]['follow_up_question_type']
            follow_up_qtn_title = follow_up_qtn[0]['follow_up_question_text']

            follow_up_qtn_response_count = self.get_response_count(follow_up_qtn, follow_up_question_type,
                                                                   is_follow_up_response=True)
            follow_up_qtn_labels = list(follow_up_qtn_response_count.keys())
            follow_up_qtn_values = list(follow_up_qtn_response_count.values())

            follow_up_qtn_obj = {
                'follow_up_title': follow_up_qtn_title,
            }
            if follow_up_question_type in ['text', 'textArea', 'textarea']:
                follow_up_qtn_obj['follow_up_table_data'] = sorted(follow_up_qtn_response_count.items(),
                                                                   key=lambda item: item[1], reverse=True)
            else:
                follow_up_qtn_obj['follow_up_chart'] = self.get_plot(follow_up_qtn_values, follow_up_qtn_labels,
                                                                     follow_up_qtn_title, follow_up_question_type)

            follow_up_data.append(follow_up_qtn_obj)

        return follow_up_data
