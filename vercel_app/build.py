import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_payroll.settings')

from django.core.management import execute_from_command_line

def handler(request, context):
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    return application(request, context)
