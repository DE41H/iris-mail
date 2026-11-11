import django.db.models.deletion
import uuid6
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0020_plugin_key_not_null'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentKey',
            fields=[
                ('id', models.UUIDField(default=uuid6.uuid7, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('prefix', models.CharField(max_length=22, unique=True)),
                ('key', models.BinaryField(max_length=32)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='keys', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
