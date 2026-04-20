from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobmatch',
            name='reason',
            field=models.TextField(blank=True),
        ),
    ]
