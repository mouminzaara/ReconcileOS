"""
Django management command to seed demo employee records for testing and demonstration.
"""

from django.core.management.base import BaseCommand
from apps.employees.models import Employee, EmployeeStatus


class Command(BaseCommand):
    help = 'Seeds initial sample employees for ReconcileOS demonstration.'

    def handle(self, *args, **options):
        sample_employees = [
            {
                "full_name": "Alice Johnson",
                "email": "alice.johnson@reconcileos.internal",
                "department": "Security & Identity",
                "status": EmployeeStatus.ACTIVE
            },
            {
                "full_name": "Bob Smith",
                "email": "bob.smith@reconcileos.internal",
                "department": "Platform Engineering",
                "status": EmployeeStatus.ACTIVE
            },
            {
                "full_name": "Carol Danvers",
                "email": "carol.danvers@reconcileos.internal",
                "department": "DevOps & Infrastructure",
                "status": EmployeeStatus.ACTIVE
            },
            {
                "full_name": "David Miller",
                "email": "david.miller@reconcileos.internal",
                "department": "Finance & Operations",
                "status": EmployeeStatus.TERMINATED
            },
            {
                "full_name": "Elena Rostova",
                "email": "elena.rostova@reconcileos.internal",
                "department": "Product Engineering",
                "status": EmployeeStatus.ACTIVE
            }
        ]

        created_count = 0
        for data in sample_employees:
            emp, created = Employee.objects.get_or_create(
                email=data['email'],
                defaults=data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {emp.full_name} ({emp.status})"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists: {emp.full_name}"))

        self.stdout.write(self.style.SUCCESS(f"Seeding completed. {created_count} employee(s) added."))
