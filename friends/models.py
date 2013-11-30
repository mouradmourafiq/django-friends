# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import signals
from django.template.loader import render_to_string
from django.utils.hashcompat import sha_constructor
from django.db.models import Q
from emailconfirmation.models import EmailAddress
from lists.models import RelationList
from notification import models as notification
from random import random
import datetime



RELATION_STATUS = (
    ("1", "Active"),
    ("2", "Inactive"),
    ("2", "Blocked"),
    )

class Contact(models.Model):
    """
    A contact is a person known by a user who may or may not themselves
    be a user.
    """
    
    # the user who created the contact
    user = models.ForeignKey(User, related_name=_("contacts"))
    
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    created_at = models.DateField(default=datetime.date.today)
    
    # the user(s) this contact correspond to
    users = models.ManyToManyField(User)
    
    def __unicode__(self):
        return "%s (%s's contact)" % (self.email, self.user)

class FriendshipManager(models.Manager):
    
    def friends_for_user(self, user):
        """
        Returns all friends for a specific user
        """
        friends = []
        for friendship in Friendship.active.all().filter(from_user=user).select_related(depth=1):
            friends.append({"friend": friendship.to_user, "friendship": friendship})
        for friendship in Friendship.active.all().filter(to_user=user).select_related(depth=1):
            friends.append({"friend": friendship.from_user, "friendship": friendship})
        return friends
    
    def in_active_relation(self, from_user, to_user):
        """
        checks if the users are in an active relation
        """
        if Friendship.active.all().filter(from_user=from_user, to_user=to_user).count() > 0:
            return True
        if Friendship.active.all().filter(from_user=to_user, to_user=from_user).count() > 0:
            return True
        return False
    
    def in_relation(self, from_user, to_user):
        """
        check if the from_user is in a relation with to_user
        """
        if self.filter(from_user=from_user, to_user=to_user).count() > 0:
            return True
        if self.filter(from_user=to_user, to_user=from_user).count() > 0:
            return True
        return False
    
    def are_friends(self, userf, usert):
        """
        Checks if the users are friends
        """
        if (Friendship.active.all().filter(from_user=userf, to_user=usert, relation_mutual=True, relation_status="1").count() > 0 and
        Friendship.active.all().filter(from_user=usert, to_user=userf, relation_status="1", relation_mutual=True).count() > 0):
            return True                    
        return False
        
    def is_follower(self, userf, usert):
        """
        checks for followship relation 
        """
        if Friendship.active.all().filter(from_user=userf, to_user=usert, relation_mutual=False).count() > 0:
            return True
        return False
        
    def is_followed(self, usert, userf):
        """
        checks for followship relation 
        """
        if Friendship.active.all().filter(from_user=userf, to_user=usert, relation_mutual=False).count() > 0:
            return True
        return False
    
    def remove_friendship(self, from_user, to_user):
        friendship = Friendship.active.all().filter(from_user=from_user, to_user=to_user)
        if friendship.count() > 0:        
            friendship[0].cancel()
        friendship = Friendship.active.all().filter(from_user=to_user, to_user=from_user)
        if friendship.count() > 0:
            friendship[0].cancel()
        
    def remove_followship(self, from_user, to_user):
        friendship = Friendship.active.all().filter(from_user=from_user, to_user=to_user)
        if friendship.count() > 0:
            friendship[0].cancel()        

class ActiveFriendshipManager(models.Manager):
    def get_query_set(self):
        return super(ActiveFriendshipManager, self).get_query_set().filter(relation_status="1")

class Friendship(models.Model):
    """
    A friendship is a bi-directional association between two users who
    have both agreed to the association.
    """
    
    
    to_user = models.ForeignKey(User, related_name="friends_to")
    from_user = models.ForeignKey(User, related_name="friends_from")
    relation_mutual = models.BooleanField()    
    created_at = models.DateField(default=datetime.date.today)
    relation_status = models.CharField(max_length=1, choices=RELATION_STATUS, default="1")
    relation_set = models.ForeignKey(RelationList, null=True, blank=True, related_name="friends_by_list") 

    
    
    objects = FriendshipManager()
    active = ActiveFriendshipManager()
    class Meta:
        unique_together = (('to_user', 'from_user'),)
    
    def block(self):
        """
        block a relation between two people
        both wouldn't be able to access to each other profile
        """
        self.relation_status = "2"
        self.save()
    
    def cancel(self):
        """
        cancel relation
        """
        self.relation_status = "2"
        self.relation_mutual  = False
        self.save()
        
    def reactivate(self):
        """
        reactivate relation
        """
        self.relation_status = "1"        
        self.save()
    
    def custom_relation_set(self, set):
        self.relation_set = set
        self.save()
        
def friend_set_for(user):
    return set([obj["friend"] for obj in Friendship.objects.friends_for_user(user)])


INVITE_STATUS = (
    ("1", "Created"),
    ("2", "Sent"),
    ("3", "Failed"),
    ("4", "Expired"),
    ("5", "Accepted"),
    ("6", "Declined"),
    ("7", "Joined Independently"),
    ("8", "Deleted")
)


class JoinInvitationManager(models.Manager):
    
    def send_invitation(self, from_user, to_email, message):
        contact, created = Contact.objects.get_or_create(email=to_email, user=from_user)
        salt = sha_constructor(str(random())).hexdigest()[:5]
        confirmation_key = sha_constructor(salt + to_email).hexdigest()
        
        accept_url = "http://%s%s" % (
            unicode(Site.objects.get_current()),
            reverse("friends_accept_join", args=(confirmation_key,)),
        )
        
        ctx = {
            "SITE_NAME": settings.SITE_NAME,
            "CONTACT_EMAIL": settings.CONTACT_EMAIL,
            "user": from_user,
            "message": message,
            "accept_url": accept_url,
        }
        
        subject = render_to_string("friends/join_invite_subject.txt", ctx)
        email_message = render_to_string("friends/join_invite_message.txt", ctx)
        
        send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [to_email])        
        return self.create(from_user=from_user, contact=contact, message=message, status="2", confirmation_key=confirmation_key)


class JoinInvitation(models.Model):
    """
    A join invite is an invitation to join the site from a user to a
    contact who is not known to be a user.
    """
    
    from_user = models.ForeignKey(User, related_name="join_from")
    contact = models.ForeignKey(Contact)
    message = models.TextField()
    sent = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=1, choices=INVITE_STATUS)
    confirmation_key = models.CharField(max_length=40)
    
    objects = JoinInvitationManager()
    
    def accept(self, new_user):
        # mark invitation accepted
        self.status = "5"
        self.save()
        # auto-create friendship
        friendship = Friendship(to_user=new_user, from_user=self.from_user)
        friendship.save()
        # notify
        if notification:
            notification.send([self.from_user], "join_accept", {"invitation": self, "new_user": new_user})
            friends = []
            for user in friend_set_for(new_user) | friend_set_for(self.from_user):
                if user != new_user and user != self.from_user:
                    friends.append(user)            


class FriendshipInvitationManager(models.Manager):
    
    def invitations(self, *args, **kwargs):                
        return self.filter(*args, **kwargs).exclude(status__in=["6", "8"])


class FriendshipInvitation(models.Model):
    """
    A frienship invite is an invitation from one user to another to be
    associated as friends.
    """
    
    from_user = models.ForeignKey(User, related_name="invitations_from")
    to_user = models.ForeignKey(User, related_name="invitations_to")
    message = models.TextField()
    sent = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=1, choices=INVITE_STATUS)    
    relationship_mutual = models.BooleanField()    
    objects = FriendshipInvitationManager()
        
    def accept(self):
        if not Friendship.objects.in_relation(self.from_user, self.to_user):     
            friendship = Friendship(to_user=self.to_user, from_user=self.from_user, relation_mutual=self.relationship_mutual)
            if self.relationship_mutual:
                    Friendship(to_user=self.from_user, from_user=self.to_user, relation_mutual=self.relationship_mutual).save()
            friendship.save()
            self.status = "5"
            self.save()
            #if notification:
                #notification.send([self.from_user], "friends_accept", {"invitation": self})                            
        else :
            etat2 = True
            try:
                friendship1 = Friendship.objects.get(to_user=self.to_user, from_user=self.from_user)
                try:
                    friendship2 = Friendship.objects.get(to_user=self.from_user, from_user=self.to_user)                    
                except:
                    etat2 = False
            except :
                try:
                    friendship1 = Friendship.objects.get(to_user=self.from_user, from_user=self.to_user)
                    user_save = self.to_user
                    self.to_user = self.from_user
                    self.from_user = user_save
                    etat2 = False
                except:
                    etat2 = False
            if friendship1.relation_mutual and self.relationship_mutual:
                friendship1.reactivate()
                friendship2.reactivate()
            elif not friendship1.relation_mutual and not self.relationship_mutual:
                friendship1.reactivate()
            elif friendship1.relation_mutual and not self.relationship_mutual:                
                friendship1.relation_mutual = self.relationship_mutual
                friendship2.relation_mutual = self.relationship_mutual
                friendship1.reactivate()
            elif not friendship1.relation_mutual and self.relationship_mutual:
                friendship1.relation_mutual = self.relationship_mutual
                friendship1.reactivate()
                if etat2:
                    friendship2.relation_mutual = self.relationship_mutual
                    friendship2.reactivate()
                else:
                    Friendship(to_user=self.from_user, from_user=self.to_user, relation_mutual=self.relationship_mutual).save()
                    
            self.status = "5"
            self.save()
            #if notification:
                #notification.send([self.from_user], "friends_accept", {"invitation": self})
            
    def decline(self):
        if not Friendship.objects.in_active_relation(self.to_user, self.from_user):
            self.status = "6"
            self.save()

    def cancel(self):
        if not Friendship.objects.in_active_relation(self.to_user, self.from_user):
            self.status = "8"
            self.save()        
    
class FriendshipInvitationHistory(models.Model):
    """
    History for friendship invitations
    """
    
    from_user = models.ForeignKey(User, related_name="invitations_from_history")
    to_user = models.ForeignKey(User, related_name="invitations_to_history")
    message = models.TextField()
    sent = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=1, choices=INVITE_STATUS)


def new_user(sender, instance, **kwargs):
        if instance.verified:
            for join_invitation in JoinInvitation.objects.filter(contact__email=instance.email):
                if join_invitation.status not in ["5", "7"]: # if not accepted or already marked as joined independently
                    join_invitation.status = "7"
                    join_invitation.save()
                    # notification will be covered below
            for contact in Contact.objects.filter(email=instance.email):
                contact.users.add(instance.user)
                # @@@ send notification
    
    # only if django-email-notification is installed
signals.post_save.connect(new_user, sender=EmailAddress)

def delete_friendship(sender, instance, **kwargs):
    friendship_invitations = FriendshipInvitation.objects.filter(to_user=instance.to_user, from_user=instance.from_user)
    for friendship_invitation in friendship_invitations:
        if friendship_invitation.status != "8":
            friendship_invitation.status = "8"
            friendship_invitation.save()


signals.pre_delete.connect(delete_friendship, sender=Friendship)


# moves existing friendship invitation from user to user to FriendshipInvitationHistory before saving new invitation
def friendship_invitation(sender, instance, **kwargs):
    friendship_invitations = FriendshipInvitation.objects.filter(to_user=instance.to_user, from_user=instance.from_user)
    for friendship_invitation in friendship_invitations:
        FriendshipInvitationHistory.objects.create(
                from_user=friendship_invitation.from_user,
                to_user=friendship_invitation.to_user,
                message=friendship_invitation.message,
                sent=friendship_invitation.sent,
                status=friendship_invitation.status
                )
        friendship_invitation.delete()


signals.pre_save.connect(friendship_invitation, sender=FriendshipInvitation)
