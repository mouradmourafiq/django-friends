# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from friends.views import commun_views as commun_views, followers as following

urlpatterns = patterns('',
    url(r'^$', following.list_followed, name='friends_list_following'),
    url(r'^(?P<username>[\w.]+)/$', following.list_followed, {'template_name' : 'friends/list_friends_profile.html'}, name='friends_list_following'),
    url(r'^random/$', following.list_random_followed, name='friends_random_list_following'),
    url(r'^random/(?P<username>[\w.]+)/$', following.list_random_followed, name='friends_random_list_following'),
    url(r'^commun/(?P<username>[\w.]+)/$', following.commun_followed, name='friends_commun_following'),
    #url(r'^remove/(?P<user_id>\d+)-(\w+)/$', commun_views.remove_relationship, name='friends_remove_following'),
    url(r'^customize/(?P<username>[\w.]+)$', commun_views.customize_relationship, 'friends_customize_following'),
)

#list management

urlpatterns += patterns('',
    url('^lists/$', commun_views.friends_by_list, name='friends_by_list_following'),
)

