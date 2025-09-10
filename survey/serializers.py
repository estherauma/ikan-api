from rest_framework import serializers
from survey.models import Survey, InlineQuestion, LearningHubProgress


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'


class InLineQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InlineQuestion
        fields = '__all__'


class LearningHubProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningHubProgress
        fields = '__all__'
