# coding: utf-8
from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest
from pyramid.view import view_config

from intranet3 import helpers as h
from intranet3.lib.bugs import Bugs
from intranet3.utils.views import ApiView


#@view_config(route_name='api_my_bugs', renderer='json', permission='can_see_own_bugs')
class BugsCollection(ApiView):

    def get(self):
        try:
            resolved = int(self.request.GET.get('resolved', 0))
        except ValueError:
            resolved = 0

        bugs = Bugs(self.request).get_user(resolved)
        bugs = sorted(bugs, cmp=h.sorting_by_severity)

        return {"bugs": [bug.to_dict() for bug in bugs]}
