"""
Django management command to seed demonstration users and RBAC profiles.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile, UserRole


class Command(BaseCommand):
    help = 'Seeds initial demonstration users for ADMIN, OPERATOR, and VIEWER roles.'

    def handle(self, *args, **options):
        users_config = [
            {
                'username': 'admin@reconcileos.internal',
                'email': 'admin@reconcileos.internal',
                'first_name': 'Admin',
                'last_name': 'Security',
                'password': 'admin123',
                'role': UserRole.ADMIN,
                'is_staff': True,
                'is_superuser': True
            },
            {
                'username': 'operator@reconcileos.internal',
                'email': 'operator@reconcileos.internal',
                'first_name': 'Operator',
                'last_name': 'SecOps',
                'password': 'operator123',
                'role': UserRole.OPERATOR,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'viewer@reconcileos.internal',
                'email': 'viewer@reconcileos.internal',
                'first_name': 'Viewer',
                'last_name': 'Auditor',
                'password': 'viewer123',
                'role': UserRole.VIEWER,
                'is_staff': False,
                'is_superuser': False
            }
        ]

        created_count = 0
        updated_count = 0

        for u_data in users_config:
            role = u_data.pop('role')
            password = u_data.pop('password')

            user, created = User.objects.get_or_create(
                username=u_data['username'],
                defaults=u_data
            )
            user.set_password(password)
            for k, v in u_data.items():
                setattr(user, k, v)
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created User: {user.username} [{role}]"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated User: {user.username} [{role}]"))

        self.stdout.write(self.style.SUCCESS(f"RBAC user seeding completed ({created_count} created, {updated_count} updated)."))
