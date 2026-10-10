from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from employees.models import Employee, default_password_for


class Command(BaseCommand):
    help = 'Create login accounts (User) for employees that do not have one yet.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Create accounts for ALL employees (including inactive/terminated). '
                 'Inactive employees are still blocked at login by the auth backend.',
        )

    def handle(self, *args, **options):
        qs = Employee.objects.filter(user__isnull=True)
        if not options['all']:
            qs = qs.filter(status='active')

        taken = set(User.objects.values_list('username', flat=True))
        batch = []
        sketched = []
        skipped = 0
        for emp in qs:
            if emp.employee_id in taken:
                skipped += 1
                continue
            user = User(
                username=emp.employee_id,
                email=emp.email or '',
                password=make_password(default_password_for(emp.employee_id)),
                first_name=emp.first_name or '',
                last_name=emp.last_name or '',
                is_active=True,
            )
            batch.append(user)
            sketched.append(emp)
            taken.add(emp.employee_id)

        created = 0
        for start in range(0, len(batch), 500):
            chunk = batch[start:start + 500]
            users = User.objects.bulk_create(chunk)
            for user, emp in zip(users, sketched[start:start + 500]):
                emp.user = user
                emp.must_change_password = emp.status == 'active'
            Employee.objects.bulk_update(sketched[start:start + 500], ['user', 'must_change_password'])
            created += len(users)

        self.stdout.write(self.style.SUCCESS(
            f'Created {created} login account(s). Skipped {skipped} (username already taken).'
        ))
        total_active = Employee.objects.filter(status='active', user__isnull=True).count()
        self.stdout.write(f'Active employees still missing a login account: {total_active}')