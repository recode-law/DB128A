from django.db import models, IntegrityError
from django.contrib.auth.models import Group, AbstractUser
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from base64 import b64encode
import secrets
import string


class User(AbstractUser):
    email = models.EmailField(unique=True)


def generate_verification_code(username: str) -> str:
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(20))

    return b64encode(f"{username}_$_{password}".encode()).decode()


class SignupRequest(models.Model):
    first_name = models.CharField(verbose_name="Vorname", max_length=100)
    last_name = models.CharField(verbose_name="Nachname", max_length=100)
    workplace = models.CharField(verbose_name="Arbeitsplatz", max_length=100)
    email = models.EmailField(verbose_name="E-Mail")
    user = models.ForeignKey(verbose_name="Benutzer", to=User, null=True, blank=True, on_delete=models.PROTECT)
    verification_code = models.TextField(verbose_name="Verifikationscode", null=True, blank=True)
    email_sent = models.BooleanField(verbose_name="E-Mail versendet", default=False)

    class Meta:
        verbose_name = "Accounterstellungsanfrage"
        verbose_name_plural = "Accounterstellungsanfragen"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}| {self.workplace} | {self.email}"

    def accept(self):
        username = self.first_name.replace(" ", "_").lower() + "_" + self.last_name.replace(" ", "_").lower()
        user = User()
        user.is_active = False
        user.username = username
        user.first_name = self.first_name
        user.last_name = self.last_name
        user.email = self.email

        try:
            user.save()
        except IntegrityError:
            number = 2
            done = False
            while not done:
                if number >= 100:
                    raise ValueError("There are too many users with the same username/email. Contact Administrator.")
                try:
                    user.username = username + str(number)
                    user.save()
                    done = True
                except IntegrityError:
                    number += 1

        group = Group.objects.get(name='Verifiziert')
        group.user_set.add(user)

        self.user = user
        self.verification_code = generate_verification_code(username)
        self.save()

    def reject(self):
        self.delete()

    def send_mail(self, request):
        subject = 'Videoverhandlung.de Verifikation'
        html_message = render_to_string('user_signup/mail_template.html', {
            'signup_request': self,
            'url_base': f'{request.scheme}://{request.get_host()}',
            'sender': f'{request.user.first_name} {request.user.last_name}'
        })
        plain_message = strip_tags(html_message)
        from_email = 'Videoverhandlung.de <kontakt@videoverhandlung.de>'
        to = self.email

        mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)

        self.email_sent = True
        self.save()