import django.forms
from django.utils.translation import ugettext_lazy as _


class SubmissionReplyForm(django.forms.Form):

    to_address = django.forms.EmailField(
        help_text=_('The email address to send this email to'),
    )
    reply_address = django.forms.EmailField(
        help_text=_('The email address the recipient will reply to'),
    )
    message = django.forms.CharField(
        widget=django.forms.Textarea(
            attrs={"rows": 5, "cols": 20}
        )
    )
