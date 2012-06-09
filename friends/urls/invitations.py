# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@license: closed application, My_licence, http://www.binpress.com/license/view/l/6f5700aefd2f24dd0a21d509ebd8cdf8

@copyright: Copyright © 2011

other contributers:
'''
from django.conf.urls.defaults import *
from friends.views import commun_views as commun_views
from friends.views import invitations as invitations

urlpatterns = patterns('',
    url(r'^$', invitations.invitations, name='friends_invitations'),
    url(r'^accept/(\w+)/$', invitations.accept_join, name='friends_accept_join'),
    # url(r'^contacts/$', commun_views.contacts, name='friends_contacts'),
)