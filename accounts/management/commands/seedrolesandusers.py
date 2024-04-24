from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import User
from decouple import config


class Command(BaseCommand):
    help = 'Seeds roles and users'
    users = ['taien+technology', 'cici+technology', 'farah+technology', 'budi+technology', 'tony+technology']

    def handle(self, *args, **kwargs):
        try:
            print('Seeding user roles')
            self.seed_users_and_roles()
        except Exception as e:
            print('Seeding user roles failed')
            print(e)

    def construct_email(self, role):
        return f'{role}@fiftyeight.io'

    def seed_users_and_roles(self):
        groups = Group.objects.bulk_create([
            Group(name='vessel_owner'),
            Group(name='taiwanese_agent'),
            Group(name='indonesian_agent'),
            Group(name='worker'),
            Group(name='buyer'),
        ])

        for i, group in enumerate(groups):
            role = Group.objects.get(name=group.name)
            user = User.objects.create_user(
                password=config('SEED_USERS_PASSWORD'),
                email=self.construct_email(self.users[i]),
                first_name='test',
                last_name='user'
            )
            user.groups.add(role)
        print('Seeding user roles successful')
