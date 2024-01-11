from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from workers.models import Worker
from workers.serializers import WorkerSerializer
from accounts.models import User
from accounts.serializers import RegisterSerializer
from common.utils import get_access_code, generate_random_password, send_email_invite
from django.contrib.auth.models import Group


class WorkerApiListView(ListCreateAPIView):
    permission_classes = ([IsAuthenticated,])
    serializer_class = WorkerSerializer
    queryset = Worker.objects.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                'status': 'OK',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    def create(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)

        email = data.get('email')
        user_exists = User.objects.filter(email=email).exists()
        if not user_exists:
            reg_data = data
            reg_data['first_name'] = data.get('f_name')
            reg_data['last_name'] = data.get('l_name')
            reg_data['password'] = generate_random_password()

            reg_serializer = RegisterSerializer(data=reg_data)
            reg_serializer.is_valid(raise_exception=True)
            user = User.objects.create_user(
                email=email,
                first_name=reg_data.get('first_name'),
                last_name=reg_data.get('last_name'),
                access_code=get_access_code(),
                is_verified=False,
                is_active=False,
            )

            group = Group.objects.get(name='worker')
            user.groups.add(group)
        else:
            user = User.objects.get(email=email)
            is_worker = user.groups.filter(name='worker').exists()
            if not is_worker:
                group = Group.objects.get(name='worker')
                user.groups.add(group)

        if not user.is_verified and not user.is_active:
            send_email_invite(user)
        else:
            data['invite_sent'] = True
            data['invite_accepted'] = True

        worker_exists = User.objects.filter(email=email).exists()
        if not worker_exists:
            data['user'] = user.id
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(created_by=request.user.id)
            return Response(
                {
                    'status': 'OK',
                    'data': serializer.data,
                    'message': 'Worker added successfully.'
                },
                status=status.HTTP_201_CREATED
            )
        else:
            # TODO: check if worker should be updated
            return Response(
                {
                    'status': 'OK',
                    'message': 'Worker already exists.'
                },
                status=status.HTTP_200_OK
            )


class WorkerApiDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = ([IsAuthenticated,])
    serializer_class = WorkerSerializer
    queryset = Worker.objects.all()

    def get_worker(self, id):
        try:
            return Worker.objects.get(id=id)
        except Worker.DoesNotExist:
            raise ValidationError('Worker does not exist')

    def retrieve(self, request, id):
        worker = self.get_worker(id=id)
        serializer = self.serializer_class(worker)
        return Response(
            {
                'status': 'OK',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    def update(self, request, id):
        worker = self.get_worker(id=id)
        serializer = self.serializer_class(worker, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user.id)
        return Response(
            {
                'status': 'OK',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, id):
        worker = self.get_worker(id=id)
        user_id = request.user.id

        if user_id != worker.created_by.id:
            return Response(
                {
                    'status': 'FAIL',
                    'data': 'You are not authorized to delete this worker'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        worker.delete()
        return Response(
            {
                'status': 'OK',
                'data': 'Worker deleted successfully'
            },
            status=status.HTTP_200_OK
        )
