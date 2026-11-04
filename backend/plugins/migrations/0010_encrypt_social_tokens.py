from django.db import migrations

from plugins.token import TokenField

_field = TokenField()


def _convert(apps, f):
    # Historical models use plain TextFields, so values are read and written raw here.
    for t in apps.get_model("socialaccount", "SocialToken").objects.all():
        t.token, t.token_secret = f(t.token), f(t.token_secret)
        t.save(update_fields=("token", "token_secret"))


def encrypt(apps, schema_editor):
    _convert(apps, _field.get_prep_value)


def decrypt(apps, schema_editor):
    _convert(apps, _field.to_python)


class Migration(migrations.Migration):
    dependencies = [
        ("plugins", "0009_plugin_version"),
        ("socialaccount", "0006_alter_socialaccount_extra_data"),
    ]

    operations = [migrations.RunPython(encrypt, decrypt)]
