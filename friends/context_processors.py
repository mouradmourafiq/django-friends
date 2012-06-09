# -*- coding: utf-8 -*-
'''
Created on Mar 01, 2011

@author: Mourad Mourafiq

@license: closed application, My_licence, http://www.binpress.com/license/view/l/6f5700aefd2f24dd0a21d509ebd8cdf8

@copyright: Copyright © 2011

other contributers:
'''
from friends.models import FriendshipInvitation

def invitations(request):
    if request.user.is_authenticated():
        return {'invitations_count': FriendshipInvitation.objects.filter(to_user=request.user, status="2").count(), }
    else:
        return {}
