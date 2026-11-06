from os import getenv

import segno
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django_otp.plugins.otp_totp.models import TOTPDevice

from plugins.models import CustomUser


class Command(BaseCommand):
    def handle(self, *args, **options):
        username, email, password = (getenv(f"DJANGO_SUPERUSER_{k}") for k in ("USERNAME", "EMAIL", "PASSWORD"))
        if not (username and email and password):
            raise CommandError("Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD.")
        if (user := CustomUser.objects.filter(username=username).first()) is None:
            try: validate_password(password)
            except ValidationError as e: raise CommandError(" ".join(e.messages))
            user = CustomUser.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f"Created superuser {username}.")
        else: self.stdout.write(f"User {username} already exists.")
        device, created = TOTPDevice.objects.get_or_create(user=user, defaults={"name": "admin"})
        self.stdout.write("Created TOTP device." if created else "Showing existing TOTP device.")
        url = device.config_url
        segno.make(url).terminal(compact=True)
        self.stdout.write(url)
