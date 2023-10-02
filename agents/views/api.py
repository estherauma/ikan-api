from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from agents.models import Agent
from agents.serializers import AgentSerializer


class AgentsApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = AgentSerializer
    queryset = Agent.objects.all()

    def list(self, request):
        agents = Agent.objects.filter(created_by=request.user.id)
        serializer = self.get_serializer(agents, many=True)
        return Response(
            {
                'status': 'OK',
                'data': serializer.data,
            },
            status.HTTP_200_OK
        )

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class AgentApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated, ])
    serializer_class = AgentSerializer
    queryset = Agent.objects.all()

    def get_agent(self, id):
        try:
            return Agent.objects.get(pk=id)
        except Agent.DoesNotExist:
            raise ValidationError('Agent does not exist')

    def retrieve(self, request, id):
        agent = self.get_agent(id)
        serializer = self.serializer_class(agent)
        return Response({
            'status': 'Ok',
            'data': serializer.data
        }, status.HTTP_200_OK)

    def update(self, request, id):
        agent = self.get_item(id)
        serializer = self.serializer_class(agent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response({
            'status': 'OK',
            'data': serializer.data
        }, status.HTTP_202_ACCEPTED)

    def destroy(self, request, id):
        agent = self.get_agent(id)
        user_id = request.user.id

        if user_id != agent.created_by.id:
            return Response({
                'status': 'FAILED',
                'error': 'Not Authorized'
            }, status.HTTP_401_UNAUTHORIZED)

        agent.delete()
        return Response({
            'status': 'OK',
            'data': id
        }, status.HTTP_200_OK)
