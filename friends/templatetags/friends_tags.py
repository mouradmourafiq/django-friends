# -*- coding: utf-8 -*-
'''
Created on Mars 01, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from django import template
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models import get_model
from django.db.models.query import QuerySet
from friends.models import Friendship
from django.utils.translation import ugettext_lazy as _
import re
from django import template
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.loading import get_model
from django.template import TemplateSyntaxError
from django.utils.functional import wraps
from django.contrib.auth.models import User
from friends.models import Friendship,FriendshipInvitation

register = template.Library()


class IfFriendsNode(template.Node):
    def __init__(self, nodelist_true, nodelist_false, *args):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.from_userP, self.to_userP = args        

    def render(self, context):
            from_user = User.objects.get(pk=int(template.resolve_variable(self.from_userP, context)))            
            to_user = User.objects.get(pk=int(template.resolve_variable(self.to_userP, context)))        
            if(Friendship.objects.are_friends(from_user, to_user)):                            
                context['message'] = 'unfriend'
                return self.nodelist_true.render(context) 
            elif(Friendship.objects.is_follower(from_user, to_user)):
                context['message'] = 'unfollow'
                return self.nodelist_true.render(context) 
            else:
                #raise template.TemplateSyntaxError('RelationshipStatus not found')        
                return self.nodelist_false.render(context)   

@register.tag
def if_friends(parser, token):
    """
    Determine if a certain type of relationship exists between two users.
    The ``status`` parameter must be a slug matching either the from_slug,
    to_slug or symmetrical_slug of a RelationshipStatus.

    Example::

        {% if_relationship from_user to_user "friends" %}
            Here are pictures of me drinking alcohol
        {% else %}
            Sorry coworkers
        {% endif_relationship %}
        
        {% if_relationship from_user to_user "blocking" %}
            damn seo experts
        {% endif_relationship %}
    """
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError, "%r takes 2 arguments:\n" % (bits[0], if_friends.__doc__)
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfFriendsNode(nodelist_true, nodelist_false, *bits[1:])


@register.inclusion_tag("friends/_relation_buttons.html", takes_context=True)
def relation_buttons(context, from_user, to_user):
    #the relation status
    status = "nothing"
    invitation = None
    #first we check if the users are in relation (friends or followers)    
    if(Friendship.objects.are_friends(from_user, to_user)):                            
        status = _('friends')                
    elif(Friendship.objects.is_follower(from_user, to_user)):
        status = _('followers')
    elif(FriendshipInvitation.objects.filter(from_user=from_user, to_user=to_user, status="2").count() > 0):
        invitation = FriendshipInvitation.objects.filter(from_user=from_user, to_user=to_user, status="2")[0]
        status = _('invited')        
    context.update({
        'status':status,
        'invitation':invitation,
        'to_user':to_user
    })
    return context

@register.filter
def add_relationship_url(user, type):
    """
    Generate a url for adding a relationship on a given user.  ``user`` is a
    User object, and ``type`` is either a relationship_status object or a 
    
    Usage:
    href="{{ user|add_relationship_url:"follow" }}"
    """
    if (type == "request"):              
        return reverse('friends_request_friends', args=[user.username])
    elif(type=="follow"):
        return reverse('friends_follow', args=[user.username])


@register.filter
def remove_relationship_url(user, type):
    """
    Generate a url for removing a relationship on a given user.  ``user`` is a
    User object, and ``status`` is either a relationship_status object or a 
    
    Usage:
    href="{{ user|remove_relationship_url:"following" }}"
    """
    if (type == "unfriend"):              
        return reverse('friends_remove_friends', args=[user.username])
    elif(type=="unfollow"):
        return reverse('friends_unfollow', args=[user.username])

#def positive_filter_decorator(func):
#    def inner(qs, user):
#        if isinstance(qs, basestring):
#            model = get_model(*qs.split('.'))
#            if not model:
#                return []
#            qs = model._default_manager.all()
#        if user.is_anonymous():
#            return qs.none()
#        return func(qs, user)
#    inner._decorated_function = getattr(func, '_decorated_function', func)
#    return wraps(func)(inner)
#
#def negative_filter_decorator(func):
#    def inner(qs, user):
#        if isinstance(qs, basestring):
#            model = get_model(*qs.split('.'))
#            if not model:
#                return []
#            qs = model._default_manager.all()
#        if user.is_anonymous():
#            return qs
#        return func(qs, user)
#    inner._decorated_function = getattr(func, '_decorated_function', func)
#    return wraps(func)(inner)
#
#@register.filter
#@positive_filter_decorator
#def friend_content(qs, user):
#    return positive_filter(qs, user.relationships.friends())
#
#@register.filter
#@positive_filter_decorator
#def following_content(qs, user):
#    return positive_filter(qs, user.relationships.following())
#
#@register.filter
#@positive_filter_decorator
#def followers_content(qs, user):
#    return positive_filter(qs, user.relationships.followers())
#
#@register.filter
#@negative_filter_decorator
#def unblocked_content(qs, user):
#    return negative_filter(qs, user.relationships.blocking())
