from rest_framework import serializers
from survey.models import Survey, InlineQuestion


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'


class InLineQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InlineQuestion
        fields = '__all__'
