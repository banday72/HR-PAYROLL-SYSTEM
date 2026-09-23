from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0008_employee_profile_picture_b64'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='reports_to',
            field=models.ForeignKey(
                blank=True,
                help_text='Direct manager this employee reports to',
                null=True,
                on_delete=models.SET_NULL,
                related_name='subordinates',
                to='employees.employee',
            ),
        ),
    ]
