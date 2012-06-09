# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@license: closed application, My_licence, http://www.binpress.com/license/view/l/6f5700aefd2f24dd0a21d509ebd8cdf8

@copyright: Copyright © 2011

other contributers:
'''
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect, render_to_response, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from friends.forms import CustomRelationForm
from friends.models import Friendship, friend_set_for
from friends.utils import *

from third_app.facebook import Facebook
from django.utils import simplejson

@login_required
def friends_names(request):
    """ return a json object containing related people names """
    q = request.GET['q'];
    user = request.user
    list_names = []
    
    friends = get_list_related_users(user=user, q=q)
    for friend in friends:        
        name = {
               'value' : friend.id,
               'name' : friend.first_name+' '+friend.last_name,                                                          
               }
        list_names.append(name)
    
    followers = get_list_related_users(user=user, mutual=False, q=q)
    for friend in followers:        
        name = {
               'value' : friend.id,
               'name' : friend.first_name+' '+friend.last_name,                                                                            
               }
        list_names.append(name)
            
    followed = get_list_related_users(user=user, mutual=False, direction='from', q=q)
    for friend in followed:        
        name = {               
               'value' : friend.id,
               'name' : friend.first_name+' '+friend.last_name,                                                             
               }
        list_names.append(name)
    
    if not list_names:
        list_names = None
    json_cals = simplejson.dumps(list_names, ensure_ascii=False)        
    return HttpResponse(json_cals, content_type='application/javascript; charset=utf-8')

@login_required
def facebook_friends_name(request):
    """ return a json object containing related people names from facebook"""
    user = request.user
    facebook_names = []
    service = user.social_auth.filter(provider='facebook')
    if service.count() > 0 : 
        service = service[0]                            
        facebook = Facebook(access_token=service.extra_data['access_token'], user_id=service.extra_data['id'])
        data = facebook.get_connections("me", "friends")
        facebook_names = data['data']
        for name in facebook_names:
            name["value"] = name.pop('id')
    if not facebook_names:
        facebook_names = None
    json_cals = simplejson.dumps(facebook_names, ensure_ascii=False)        
    return HttpResponse(json_cals, content_type='application/javascript; charset=utf-8')         
            
                
#
#@login_required
#def remove_relationship(request, user_id, type, public_profile_field=None,
#                      template_name='profiles/profile_list.html',
#                      extra_context=None):
#    """
#        this view serves for both relationships: follwship and friendship
#    """
#    to_user = User.objects.get(pk=user_id)
#    if type == "friendship":
#        Friendship.objects.remove_friendship(from_user=request.user, to_user=to_user)        
#    elif type == "followship":
#        Friendship.objects.remove_followship(from_user=request.user, to_user=to_user)
#    return HttpResponseRedirect('/profiles/')


@login_required
def customize_relationship(request, username,
                           success_url=None,
                           form_class=CustomRelationForm,
                           extra_context=None,
                           template_name="friends/cstomize_relation.html"):
    """
    customize relationship view
    """
    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        first_user = request.user
        second_user = User.objects.get(username=username)
        if form.is_valid():
            friendship = form.save(first_user, second_user)
            # success_url needs to be dynamically generated here; setting a
            # a default value using reverse() will cause circular-import
            # problems with the default URLConf for this application, which
            # imports this file.
        

            #return
            return HttpResponseRedirect(success_url or reverse('firends_list_friends'))
    else:
        form = form_class()
    
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value
    return render_to_response(template_name,
                              { 'form': form },
                              context_instance=context)
    

@login_required
def friends_by_list(request):
    """displays friends by lists and sublists """

#def contacts(request, form_class=ImportVCardForm,
#        template_name="friends/contacts.html"):
#    if request.method == "POST":
#        if request.POST["action"] == "upload_vcard":
#            import_vcard_form = form_class(request.POST, request.FILES)
#            if import_vcard_form.is_valid():
#                imported, total = import_vcard_form.save(request.user)
#                request.user.message_set.create(message=_("%(total)s vCards found, %(imported)s contacts imported.") % {'imported': imported, 'total': total})
#                import_vcard_form = ImportVCardForm()
#    else:
#        import_vcard_form = form_class()
#    
#    return render_to_response(template_name, {
#        "import_vcard_form": import_vcard_form,
#    }, context_instance=RequestContext(request))
#contacts = login_required(contacts)

def friends_objects(request, template_name, friends_objects_function, extra_context={}):
    """
    Display friends' objects.
    
    This view takes a template name and a function. The function should
    take an iterator over users and return an iterator over objects
    belonging to those users. This iterator over objects is then passed
    to the template of the given name as ``object_list``.
    
    The template is also passed variable defined in ``extra_context``
    which should be a dictionary of variable names to functions taking a
    request object and returning the value for that variable.
    """
    
    friends = friend_set_for(request.user)
    
    dictionary = {
        "object_list": friends_objects_function(friends),
    }
    for name, func in extra_context.items():
        dictionary[name] = func(request)
    
    return render_to_response(template_name, dictionary, context_instance=RequestContext(request))
friends_objects = login_required(friends_objects)

