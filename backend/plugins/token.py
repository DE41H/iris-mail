from allauth.socialaccount.models import SocialToken
from encrypted_fields.fields import EncryptedTextField


class TokenField(EncryptedTextField):
    def get_prep_value(self, value):
        return super().get_prep_value(value) or value

    def deconstruct(self):
        name, _, args, kwargs = super().deconstruct()
        return name, "django.db.models.TextField", args, kwargs


for name in ("token", "token_secret"):
    SocialToken._meta.get_field(name).__class__ = TokenField  # pyright: ignore[reportAttributeAccessIssue]
