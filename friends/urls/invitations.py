# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from friends.views import commun_views as commun_views
from friends.views import invitations as invitations

urlpatterns = patterns('',
    url(r'^$', invitations.invitations, name='friends_invitations'),
    url(r'^accept/(\w+)/$', invitations.accept_join, name='friends_accept_join'),
    # url(r'^contacts/$', commun_views.contacts, name='friends_contacts'),
)
