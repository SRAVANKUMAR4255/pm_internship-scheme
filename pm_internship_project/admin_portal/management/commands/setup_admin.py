from django.core.management.base import BaseCommand
from student_portal.models import CustomUser


class Command(BaseCommand):
    help = 'Create the default admin account for the PM Internship Portal'

    def handle(self, *args, **kwargs):
        email = 'admin@pm-internship.gov.in'
        if not CustomUser.objects.filter(email=email).exists():
            CustomUser.objects.create_user(
                email=email,
                full_name='Portal Administrator',
                password='admin',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(
                'Admin account created successfully!\n'
                'Username: admin\n'
                'Password: admin\n'
                'Login at: /admin-portal/login/'
            ))
        else:
            self.stdout.write(self.style.WARNING('Admin account already exists.'))
