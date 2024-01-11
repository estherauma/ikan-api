from rest_framework import serializers
from workers.models import Worker
from accounts.models import User


class WorkerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = Worker
        fields = '__all__'
