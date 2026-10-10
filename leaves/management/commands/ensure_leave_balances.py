from datetime import date

from django.core.management.base import BaseCommand

from employees.models import Employee
from leaves.models import LeaveBalance, LeaveType


class Command(BaseCommand):
    help = 'Create annual leave balances for all active employees (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, default=None, help='Year to allocate (default: current)')

    def handle(self, *args, **options):
        year = options['year'] or date.today().year
        leave_types = list(LeaveType.objects.all())
        employees = list(Employee.objects.filter(status='active'))

        existing = set(LeaveBalance.objects.filter(year=year).values_list('employee_id', 'leave_type_id'))
        rows = [
            LeaveBalance(employee=emp, leave_type=lt, year=year, allocated=lt.days_per_year)
            for emp in employees
            for lt in leave_types
            if (emp.id, lt.id) not in existing
        ]

        created = 0
        for start in range(0, len(rows), 500):
            created += len(LeaveBalance.objects.bulk_create(rows[start:start + 500]))

        self.stdout.write(self.style.SUCCESS(
            f'Allocated {year} balances: {created} row(s) created for '
            f'{len(employees)} active employees.'
        ))