# Generated by Django 5.1.6 on 2025-03-19 20:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('to_do_app', '0003_alter_task_options_task_priority_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskShare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.CharField(choices=[('VIEW', 'View Only'), ('EDIT', 'Can Edit'), ('DELETE', 'Can Delete')], default='VIEW', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shared_with', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_shares', to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shares', to='to_do_app.task')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('task', 'shared_with')},
            },
        ),
        migrations.AddField(
            model_name='task',
            name='shared_with',
            field=models.ManyToManyField(related_name='shared_tasks', through='to_do_app.TaskShare', to=settings.AUTH_USER_MODEL),
        ),
    ]
