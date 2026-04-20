import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0003_jobmatch_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobmatch',
            name='calculated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
