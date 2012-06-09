# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@license: closed application, My_licence, http://www.binpress.com/license/view/l/6f5700aefd2f24dd0a21d509ebd8cdf8

@copyright: Copyright © 2011

other contributers:
'''
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from friends.models import JoinInvitation, FriendshipInvitation, Friendship
from notification import models as notification

# not touched
class UserForm(forms.Form):
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)


class JoinRequestForm(forms.Form):
    
    email = forms.EmailField(label=_("Email"), required=True)
    message = forms.CharField(label=_("Message"), required=False, widget=forms.Textarea(attrs={'cols': '40', 'rows': '8'}))
    
    def clean_email(self):
        # @@@ this assumes email-confirmation is being used            
        if User.objects.filter(email=self.cleaned_data["email"]).count()>0:
            raise forms.ValidationError(_("Someone with that email address is already here."))
        return self.cleaned_data[_("email")]
    
    def save(self, user):
        join_request = JoinInvitation.objects.send_invitation(user, self.cleaned_data["email"], self.cleaned_data["message"])
        #user.message_set.create(message="Invitation to join sent to %s" % join_request.contact.email)
        return join_request


class InviteFriendForm(UserForm):
    
    to_user = forms.CharField(widget=forms.HiddenInput)
    message = forms.CharField(label=_("Message"), required=False, widget=forms.Textarea(attrs={'rows': '12', 'cols':'55'}))
    error_css_class = "error"
    
    def clean_to_user(self):
        to_username = self.cleaned_data["to_user"]
        try:
            User.objects.get(username=to_username)
        except User.DoesNotExist:
            raise forms.ValidationError("Unknown user.")
            
        return self.cleaned_data["to_user"]
    
    def clean(self):
        to_user = User.objects.get(username=self.cleaned_data["to_user"])
        previous_invitations_to = FriendshipInvitation.objects.invitations(to_user=to_user, from_user=self.user)
        if previous_invitations_to.count() > 0:
            raise forms.ValidationError(_("Already requested friendship with %s") % to_user.username)
        # check inverse
        previous_invitations_from = FriendshipInvitation.objects.invitations(to_user=self.user, from_user=to_user)
        if previous_invitations_from.count() > 0:
            raise forms.ValidationError(_("%s has already requested friendship with you") % to_user.username)
        return self.cleaned_data
    
    def save(self):
        to_user = User.objects.get(username=self.cleaned_data["to_user"])
        message = self.cleaned_data["message"]
        invitation = FriendshipInvitation(from_user=self.user, to_user=to_user, message=message, status="2")
        invitation.save()
        if notification:
            notification.send([to_user], "friends_invite", {"invitation": invitation})            
        #self.user.message_set.create(message="Friendship requested with %s" % to_user.username) # @@@ make link like notification
        return invitation
            
#not touched
    
REALTION_CHOICES = (('1', 'single'),
                    ('2', 'in a relation'),
                    ('3', 'engaged'),
                    ('4', 'it\'s complicated'),
                    ('5', 'separated'),
                    ('6', 'classmate'),
                    ('7', 'co-worker'),)

class CustomRelationForm(forms.Form):
    custom_relation = forms.ChoiceField(choices=REALTION_CHOICES)
    error_css_class = "error"
    
    def save(self, first_user, second_user):
        friendship = Friendship.objects.filter(Q(relation_mutual=True), Q(to_user=first_user) | Q(from_user=first_user)).filter(
                                        Q(relation_mutual=True), Q(to_user=second_user) | Q(from_user=second_user))
        friendship.custom_relation = self.custom_relation
        friendship.objects.save()
