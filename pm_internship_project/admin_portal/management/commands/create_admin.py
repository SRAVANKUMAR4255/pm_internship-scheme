from django.core.management.base import BaseCommand
from student_portal.models import CustomUser


class Command(BaseCommand):
    help = 'Create default admin account'

    def handle(self, *args, **kwargs):
        email = 'admin@portal.gov.in'
        if not CustomUser.objects.filter(email=email).exists():
            CustomUser.objects.create_user(
                email=email, full_name='Portal Admin',
                password='admin', role='admin'
            )
            self.stdout.write(self.style.SUCCESS('Admin created. Username: admin | Password: admin'))
        else:
            self.stdout.write(self.style.WARNING('Admin already exists.'))