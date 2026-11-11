from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0019_usage_date_noindex'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='plugin',
            name='plugin_key_prefix_together',
        ),
        migrations.AlterField(
            model_name='plugin',
            name='key',
            field=models.BinaryField(max_length=32),
        ),
        migrations.AlterField(
            model_name='plugin',
            name='prefix',
            field=models.CharField(max_length=16, unique=True),
        ),
    ]
