from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from wagtail.admin import messages
from wagtail.contrib.forms.utils import get_forms_for_user
from wagtail.contrib.forms.views import SubmissionsListView
from wagtail.core.models import Page

from .forms import SubmissionReplyForm


class ReplySubmissionView(TemplateView):
    """
    Reply to a contact form submission

    :success_url    can continue to be the default wagtailforms:list_submission url
                    because that view is overwritten by the `list_submissions` url
                    from the wagtail_contact_reply package.
    """
    template_name = 'wagtailforms/reply.html'
    success_url = 'wagtailforms:list_submissions'
    page = None
    http_method_names = ['get', 'post']

    def get_success_url(self):
        """Returns the success URL to redirect to after a successful email was sent."""
        return self.success_url

    def dispatch(self, request, *args, **kwargs):
        """Check permissions, set the page and submissions, handle reply email."""
        page_id = kwargs.get('page_id')
        submission_id = kwargs.get('submission_id')

        if not get_forms_for_user(self.request.user).filter(id=page_id).exists():
            raise PermissionDenied

        self.page = get_object_or_404(Page, id=page_id).specific

        submission_class = self.page.get_submission_class()
        submission = submission_class._default_manager.get(id=submission_id)

        # Look for email field
        email_field_name = False
        for field in self.page.get_form_fields():
            if field.field_type == 'email':
                email_field_name = field.clean_name

        if not email_field_name:
            # There is no email field in this form. Can't reply to someone who
            # doesn't have an email address
            raise PermissionDenied

        # Dictionary comprehension to generate name-to-label keys
        data_fields = {name: label for name, label in self.page.get_data_fields()}
        submission_data = submission.get_data()
        self.submission = ((data_fields.get(key), value) for key, value in submission_data.items())

        self.form = SubmissionReplyForm(
            request.POST or None,
            initial={
                'to_address': submission_data.get(email_field_name),
                'reply_address': self.page.from_address,
            },
        )

        if request.method == 'POST' and self.form.is_valid():
            email_success = False
            try:
                email = EmailMessage(
                    f"Re: {self.page.subject}",
                    self.form.cleaned_data["message"],
                    self.page.from_address,
                    [self.form.cleaned_data["to_address"]],
                    reply_to=[self.form.cleaned_data["reply_address"]],
                )
                email.send()
                email_success = True
            except TypeError:
                messages.warning(
                    self.request,
                    _("Invalid to, from, or reply addresses"),
                )

            if email_success:
                messages.success(
                    self.request,
                    _('Reply was email sent'),
                )
                return redirect(self.get_success_url(), page_id)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Get the context for this view"""
        context = super().get_context_data(**kwargs)

        context.update({
            'page': self.page,
            'submission': self.submission,
            'form': self.form,
        })

        return context


class ReplySubmissionsListView(SubmissionsListView):
    """
    Lists submissions for the provided form page

    Other than checking if the form_page has any email fields in it,
    this is almost no different than the SubmiionsListView it inherits from.
    """

    def dispatch(self, request, *args, **kwargs):
        # Add the form_page to the kwargs for when SubmissionsListView.dispatch() is run
        self.form_page = get_object_or_404(Page, pk=kwargs['page_id']).specific
        kwargs['form_page'] = self.form_page
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Most of the heavy listing was performed in SubmissionsListView.get_context_data()
        # Leverage as much of the processing that's already been complete.
        # We just need to check if the main form as an email address field and pass it
        # into the template context.
        context = super().get_context_data(**kwargs)

        # Look for email field
        has_email_field = False
        for field in self.form_page.get_form_fields():
            if field.field_type == 'email':
                has_email_field = True
                break

        context.update({
            'has_email_field': has_email_field,
        })

        return context
