# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@license: closed application, My_licence, http://www.binpress.com/license/view/l/6f5700aefd2f24dd0a21d509ebd8cdf8

@copyright: Copyright © 2011

other contributers:
'''
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from friends.forms import JoinRequestForm
from friends.models import FriendshipInvitation, JoinInvitation
from registration.forms import RegistrationFormUniqueEmail
from django.utils import simplejson
from notification import models as notification
from profiles.models import ProfileStats

@login_required
def invitations(request, form_class=JoinRequestForm,
        template_name="friends/invitations.html"):
    response = {'success':False}
    if request.method == "POST":
        invitation_id = request.POST.get("invitation", None)
        if request.POST["action"] == "accept":
            try:
                invitation = FriendshipInvitation.objects.get(id=invitation_id)
                if invitation.to_user == request.user:
                    invitation.accept()
                    if notification:
                        notification.send([invitation.from_user], "friends_accept", {"invitation": invitation})
                    #request.user.message_set.create(message=_("Accepted friendship request from %(from_user)s") % {'from_user': invitation.from_user})
                    #stats
                    from_user_stats = ProfileStats.objects.get(user=invitation.from_user)
                    from_user_stats.friends = int(from_user_stats.friends) + 1
                    from_user_stats.save()
                    to_user_stats = ProfileStats.objects.get(user=invitation.to_user)
                    to_user_stats.friends = int(to_user_stats.friends) + 1
                    to_user_stats.save()
                    response = {'success':True}                    
            except FriendshipInvitation.DoesNotExist:
                pass
            join_request_form = form_class()
        elif request.POST["action"] == "invite": # invite to join
            join_request_form = form_class(request.POST)
            if join_request_form.is_valid():
                join_request_form.save(request.user)
                join_request_form = form_class() # @@@
                response = {'success':True}
        elif request.POST["action"] == "decline":
            try:
                invitation = FriendshipInvitation.objects.get(id=invitation_id)
                if invitation.to_user == request.user:
                    invitation.decline()
                    #request.user.message_set.create(message=_("Declined friendship request from %(from_user)s") % {'from_user': invitation.from_user})
                    response = {'success':True}
            except FriendshipInvitation.DoesNotExist:
                pass
            join_request_form = form_class()
        elif request.POST["action"] == "cancel":
            try:
                invitation = FriendshipInvitation.objects.get(id=invitation_id)
                if invitation.from_user == request.user:
                    invitation.cancel()
                    #request.user.message_set.create(message=_("Declined friendship request from %(from_user)s") % {'from_user': invitation.from_user})
                    response = {'success':True}
                    if not request.is_ajax():
                        return HttpResponseRedirect(reverse('profiles_profile_detail',
                              kwargs={ 'username': invitation.to_user.username }))
            except FriendshipInvitation.DoesNotExist:
                pass
            join_request_form = form_class()
        if request.is_ajax(): 
            json_response = simplejson.dumps(response)           
            return HttpResponse(json_response, mimetype="application/json")
    else:
        join_request_form = form_class()
    
    invites_received = request.user.invitations_to.invitations().order_by("-sent")
    invites_sent = request.user.invitations_from.invitations().order_by("-sent")
    joins_sent = request.user.join_from.all().order_by("-sent")
    
    return render_to_response(template_name, {
        "join_request_form": join_request_form,
        "invites_received": invites_received,
        "invites_sent": invites_sent,
        "joins_sent": joins_sent,
    }, context_instance=RequestContext(request))
    

def accept_join(request, confirmation_key, form_class=RegistrationFormUniqueEmail,
        template_name='registration/registration_form.html'):
    join_invitation = get_object_or_404(JoinInvitation, confirmation_key=confirmation_key.lower())
    if request.user.is_authenticated():
        return render_to_response('registration/registration_form.html', {
        }, context_instance=RequestContext(request))
    else:
        form = form_class(initial={"email": join_invitation.contact.email, "confirmation_key": join_invitation.confirmation_key })                
        return render_to_response(template_name, {
            "form": form,
        }, context_instance=RequestContext(request))
