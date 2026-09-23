import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_payroll.settings')

import django
django.setup()

from django.core.management import call_command
try:
    call_command('migrate', '--run-syncdb', '--noinput', verbosity=0)
except Exception:
    pass

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

def handler(request):
    status_code = 200
    headers_dict = {}

    def start_response(status, headers, exc_info=None):
        nonlocal status_code, headers_dict
        status_code = int(status.split(' ', 1)[0])
        headers_dict = dict(headers)

    response_body = b''.join(application(request.environ, start_response))

    return {
        'statusCode': status_code,
        'headers': headers_dict,
        'body': response_body.decode('utf-8', errors='replace'),
    }
