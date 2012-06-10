# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@copyright: Copyright © 2011

other contributers:
'''
from friends.models import FriendshipInvitation

def invitations(request):
    if request.user.is_authenticated():
        return {'invitations_count': FriendshipInvitation.objects.filter(to_user=request.user, status="2").count(), }
    else:
        return {}
