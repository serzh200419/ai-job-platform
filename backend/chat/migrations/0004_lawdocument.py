from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_chatsession_profile_summary'),
    ]

    operations = [
        migrations.CreateModel(
            name='LawDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=500)),
                ('content', models.TextField()),
                ('embedding', models.JSONField(default=list)),
                ('chunk_index', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['chunk_index'],
            },
        ),
    ]
