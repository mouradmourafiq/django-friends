# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import HttpResponseRedirect, render_to_response, HttpResponse
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from friends.models import Friendship
from friends.utils import get_list_related_users
from notification import models as notification
from django.utils import simplejson
from profiles.models import ProfileStats

@login_required
def follow(request, username,  public_profile_field=None,
                   template_name='profiles/profile_list.html',
                   extra_context=None):    
        from_user= request.user
        to_user = User.objects.get(username=username)
        #follower friendship type 
        friendship = Friendship.objects.filter(from_user=from_user, to_user=to_user)
        if friendship.count() >0:
            friendship[0].reactivate()            
        else:                
            friendship = Friendship(from_user=from_user, to_user=to_user, relation_mutual=False)
            friendship.save()
        if notification:
            notification.send([to_user], "new_follower", {"new_follower": from_user})   
        #stats
        from_user_stats = ProfileStats.objects.get(user=from_user)
        from_user_stats.following = int(from_user_stats.following) + 1
        from_user_stats.save()
        to_user_stats = ProfileStats.objects.get(user=to_user)
        to_user_stats.followers = int(to_user_stats.followers) + 1
        to_user_stats.save()
        response = {'success':True}
        if request.is_ajax(): 
            json_response = simplejson.dumps(response)           
            return HttpResponse(json_response, mimetype="application/json")                     
        return HttpResponseRedirect(reverse('profiles_profile_detail',
                              kwargs={ 'username': username }))

@login_required
def unfollow(request, username, public_profile_field=None,
                      template_name='profiles/profile_list.html',
                      extra_context=None):
    """
        this view serves for both relationships: follwship and friendship
    """    
    to_user = User.objects.get(username=username)
    from_user = request.user
    Friendship.objects.remove_followship(from_user=from_user, to_user=to_user)
    #stats
    from_user_stats = ProfileStats.objects.get(user=from_user)
    from_user_stats.following = int(from_user_stats.following) - 1
    from_user_stats.save()
    to_user_stats = ProfileStats.objects.get(user=to_user)
    to_user_stats.followers = int(to_user_stats.followers) - 1
    to_user_stats.save()
    response = {'success':True}
    if request.is_ajax(): 
            json_response = simplejson.dumps(response)           
            return HttpResponse(json_response, mimetype="application/json")  
    return HttpResponseRedirect(reverse('profiles_profile_detail',
                              kwargs={ 'username': username }))

@login_required
def list_followers(request, username=None, template_name="friends/list_friends.html"):
    if username is None:
        user = request.user   
    else:
        user = User.objects.get(username=username)   
    followers = get_list_related_users(user=user, mutual=False)
    return render_to_response(template_name, {
        "list_friends" : followers,
        "class" : "a.a_followers",
        "user_profile" : user,
        "type" : "Followers",
    }, context_instance=RequestContext(request))

def list_random_followers(request, username=None, template_name="friends/random_friends.html"):
    if username is None:
        user = request.user   
    else:
        user = User.objects.get(username=username)   
    followers = get_list_related_users(user=user, mutual=False, random=True)    
    return render_to_response(template_name, {
        "list_friends" : followers,
    }, context_instance=RequestContext(request))

@login_required
def list_followed(request, username=None, template_name="friends/list_friends.html"):
    if username is None:
        user = request.user   
    else:
        user = User.objects.get(username=username)
    followed = get_list_related_users(user=user, mutual=False, direction='from')
    return render_to_response(template_name, {
        "list_friends" : followed,
        "class" : "a.a_following",
        "user_profile" : user,
        "type" : "Following",
    }, context_instance=RequestContext(request))

def list_random_followed(request, username=None, template_name="friends/random_friends.html"):
    if username is None:
        user = request.user   
    else:
        user = User.objects.get(username=username) 
    followed = get_list_related_users(user=user, mutual=False, direction='from', random=True)    
    return render_to_response(template_name, {
        "list_friends" : followed,
    }, context_instance=RequestContext(request))
    
@login_required
def commun_follwers(request, username, public_profile_field=None,
                   template_name='friends/list_friends.html',
                   extra_context=None):
    first_user = request.user
    second_user = User.objects.get(username=username)
    followers_for_first = get_list_related_users(user=first_user, mutual=False)
    commun_followers = []
    for u in followers_for_first:
        if Friendship.objects.is_follower(u, second_user):            
            commun_followers.append(u)
            
    return render_to_response(template_name, {
        "list_friends" : commun_followers,
    }, context_instance=RequestContext(request))

@login_required
def commun_followed(request, username, public_profile_field=None,
                   template_name='friends/list_friends.html',
                   extra_context=None):
    first_user = request.user
    second_user = User.objects.get(username=username)
    followed_for_first = get_list_related_users(user=first_user, mutual=False, direction='from')
    commun_followed = []
    for u in followed_for_first:
        if Friendship.objects.is_followed(u, second_user):            
            commun_followed.append(u)
            
    return render_to_response(template_name, {
        "list_friends" : commun_followed,
    }, context_instance=RequestContext(request))
