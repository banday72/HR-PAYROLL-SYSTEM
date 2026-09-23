from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0007_employee_face_data_employee_face_registered'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='profile_picture_b64',
            field=models.TextField(blank=True, help_text='Base64 encoded profile picture for Vercel'),
        ),
    ]
