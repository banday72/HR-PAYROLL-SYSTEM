import logging

logger = logging.getLogger('employees')


def log_audit(user=None, action='', model_name='', object_id='', description='', request=None):
    from .models import AuditLog
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        description=description,
        ip_address=ip_address,
    )
    logger.info(f"{user} - {action} - {model_name}:{object_id} - {description}")
