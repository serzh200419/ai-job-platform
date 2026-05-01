from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='profile_summary',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
