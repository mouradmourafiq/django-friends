# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import HttpResponseRedirect, render_to_response, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from friends.models import FriendshipInvitation, Friendship
from friends.utils import get_list_related_users
from notification import models as notification
from django.utils import simplejson
from profiles.models import ProfileStats
import datetime

@login_required
def request_friendship(request, username, public_profile_field=None,
                   template_name='profiles/profile_list.html',
                   extra_context=None):    
    to_user = User.objects.get(username=username)
 
    invitation, created = FriendshipInvitation.objects.get_or_create(from_user=request.user, to_user=to_user, message='friendship request', status='2', relationship_mutual=True)    
    if notification and created:
        notification.send([to_user], "friends_invite", {"invitation": invitation})
    response = {'success':True}
    if request.is_ajax(): 
            json_response = simplejson.dumps(response)           
            return HttpResponse(json_response, mimetype="application/json")                                        
    return HttpResponseRedirect(reverse('profiles_profile_detail',
                          kwargs={ 'username': username }))

@login_required
def remove_friend(request, username, public_profile_field=None,
                      template_name='profiles/profile_list.html',
                      extra_context=None):
    """
        this view serves for both relationships: follwship and friendship
    """
    to_user = User.objects.get(username=username)
    from_user = request.user
    Friendship.objects.remove_friendship(from_user=from_user, to_user=to_user)
    #stats
    from_user_stats = ProfileStats.objects.get(user=from_user)
    from_user_stats.friends = int(from_user_stats.friends) - 1
    from_user_stats.save()
    to_user_stats = ProfileStats.objects.get(user=to_user)
    to_user_stats.friends = int(to_user_stats.friends) - 1
    to_user_stats.save()
    response = {'success':True}
    if request.is_ajax(): 
            json_response = simplejson.dumps(response)           
            return HttpResponse(json_response, mimetype="application/json")                    
    return HttpResponseRedirect(reverse('profiles_profile_detail',
                              kwargs={ 'username': username }))

@login_required
def friends_request(request, template_name="friends/friends_request.html"):
    invites_received = request.user.invitations_to.invitations().order_by("-sent")
    return render_to_response(template_name, {
        "invites_received" : invites_received,
    }, context_instance=RequestContext(request))

@login_required
def freinds_sent(request, template_name="friends/friends_sent.html"):
    invites_sent = request.user.invitations_from.invitations().order_by("-sent")
    return render_to_response(template_name, {
        "invites_sent" : invites_sent,
    }, context_instance=RequestContext(request))
    
@login_required
def list_friends(request, username=None, template_name="friends/list_friends.html"):
    if username is None:
        user = request.user   
    else:
        user = User.objects.get(username=username)   
    friends = get_list_related_users(user=user)
    return render_to_response(template_name, {
        "list_friends" : friends,
        "class"  : "a.a_friends",
        "user_profile" : user,
        "type" : "Friends",
    }, context_instance=RequestContext(request))
    
def list_random_friends(request, username=None, template_name="friends/random_friends.html"):
    if username is None:
        user = request.user   
    else:
        user = User.objects.get(username=username)   
    friends = get_list_related_users(user=user, random=True)
    return render_to_response(template_name, {
        "list_friends" : friends,
    }, context_instance=RequestContext(request))

@login_required
def commun_friends(request, username, public_profile_field=None,
                   template_name='friends/list_friends.html',
                   extra_context=None):
    first_user = request.user
    second_user = User.objects.get(username=username)
    friends_for_first = get_list_related_users(user=first_user)
    commun_friends = []
    for u in friends_for_first:
        if Friendship.objects.are_friends(second_user, u):            
            commun_friends.append(u)
            
    return render_to_response(template_name, {
        "list_friends" : commun_friends,
    }, context_instance=RequestContext(request))

@login_required
def friends_birthdays(request):
    """return a list of friends birthdays"""
    list_birthdays = []
    friends = get_list_related_users(user=request.user, mutual=False)
    start = request.GET['start']
    start = datetime.date.fromtimestamp(int(start))
    end = request.GET['end']
    end = datetime.date.fromtimestamp(int(end))
    
    for friend in friends:
        profile = friend.get_profile()
        birth_date = profile.birthday
        if birth_date:
            if (start.month == 12 and end.month == 2):
                birth_date = birth_date.replace(year = end.year)
            else :
                birth_date = birth_date.replace(year = start.year)
            if (birth_date >= start and birth_date <= end):                
                birthday = {               
                       'title' : _("%s\'s birthday") % friend.username,
                       'allDay' : True,
                       'color' : '#a2168b',
                       'start' : datetime.datetime.combine(birth_date, datetime.time()).strftime('%Y-%m-%dT%H:%M:%S'),               
                       'url' : profile.get_absolute_url(),               
                       }
                list_birthdays.append(birthday)
    
    if not list_birthdays:
        list_birthdays = None
    json_cals = simplejson.dumps(list_birthdays, ensure_ascii=False)        
    return HttpResponse(json_cals, content_type='application/javascript; charset=utf-8')
