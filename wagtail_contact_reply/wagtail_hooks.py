from django.conf.urls import url
from django.http import HttpResponse
from wagtail.core import hooks

from .views import ReplySubmissionsListView, ReplySubmissionView


def admin_view(request):
  return HttpResponse(
    "I have approximate knowledge of many things!",
    content_type="text/plain")

@hooks.register('register_admin_urls')
def urlconf_time():

    return [
        url(r'^forms/submissions/(?P<page_id>\d+)/$', ReplySubmissionsListView.as_view(), name='list_submissions'),
        url(r'^forms/submissions/(?P<page_id>\d+)/reply/(?P<submission_id>\d+)/$', ReplySubmissionView.as_view(), name='reply_submissions'),
    ]
