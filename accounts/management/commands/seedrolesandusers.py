from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import User
from decouple import config


class Command(BaseCommand):
    help = 'Seeds roles and users'
    users = ['taien+technology', 'cici+technology', 'farah+technology',
             'budi+technology', 'tony+technology', 'public+technology']

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
        role_names = ['vessel_owner', 'taiwanese_agent',
                      'indonesian_agent', 'worker', 'buyer', 'public', 'trader', 'admin']
        roles = []

        for role_name in role_names:
            role, _ = Group.objects.get_or_create(name=role_name)
            roles.append(role)

        for i, role in enumerate(roles):
            email = self.construct_email(self.users[i])
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'password': config('SEED_USERS_PASSWORD'),
                    'first_name': 'test',
                    'last_name': 'user'
                }
            )
            if created:
                user.set_password(config('SEED_USERS_PASSWORD'))
                user.save()
            user.groups.add(role)
        print('Seeding user roles successful')
