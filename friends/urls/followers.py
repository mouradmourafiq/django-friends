# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django.conf.urls.defaults import *
from friends.views import commun_views as commun_views, followers as followers

urlpatterns = patterns('',
    url(r'^$', followers.list_followers, name='friends_list_followers'),
    url(r'^(?P<username>[\w.]+)/$', followers.list_followers, {'template_name' : 'friends/list_friends_profile.html'}, name='friends_list_followers'),
    url(r'^random/$', followers.list_random_followers, name='friends_random_list_followers'),
    url(r'^random/(?P<username>[\w.]+)/$', followers.list_random_followers, name='friends_random_list_followers'),
    url(r'^commun/(?P<username>[\w.]+)/$', followers.commun_follwers, name='friends_commun_followers'),
    url(r'^unfollow/(?P<username>[\w.]+)/$', followers.unfollow, name='friends_unfollow'),
    url(r'^customize/(?P<username>[\w.]+)$', commun_views.customize_relationship, 'friends_customize_followers'),
    url(r'^request/(?P<username>[\w.]+)/$', followers.follow, name='friends_follow'),
)

#list management

urlpatterns += patterns('',
    url('^lists/$', commun_views.friends_by_list, name='friends_by_list_followers'),
)
