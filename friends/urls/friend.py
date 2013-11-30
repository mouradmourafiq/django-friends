# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from friends.views import commun_views as commun_views, friend as friends

urlpatterns = patterns('',
    url(r'^list/$', friends.list_friends, name='friends_list_friends'),
    url(r'^list_names/$', commun_views.friends_names, name='friends_list_names'),
    url(r'^facebook_names/$', commun_views.facebook_friends_name, name='friends_facebook_names'),
    url(r'^list/(?P<username>[\w.]+)/$', friends.list_friends,{'template_name' : 'friends/list_friends_profile.html'}, name='friends_list_friends'),
    url(r'^random/$', friends.list_random_friends, name='friends_random_list_friends'),
    url(r'^random/(?P<username>[\w.]+)/$', friends.list_random_friends, name='friends_random_list_friends'),
    url(r'^sent/$', friends.freinds_sent, name='friends_sent'),
    url(r'^requests/$', friends.friends_request, name='friends_request'),
    url(r'^commun/(?P<username>[\w.]+)/$', friends.commun_friends, name='friends_commun_friends'),
    url(r'^remove/(?P<username>[\w.]+)/$', friends.remove_friend, name='friends_remove_friends'),
    url(r'^customize/(?P<username>[\w.]+)$', commun_views.customize_relationship, 'friends_customize_friends'),
    url(r'^request/(?P<username>[\w.]+)/$', friends.request_friendship, name='friends_request_friends'),
    url(r'^birthdays/$', friends.friends_birthdays, name='friends_birthdays'),
)

#list management

urlpatterns += patterns('',
    url('^lists/$', commun_views.friends_by_list, name='friends_by_list_friends'),
)
