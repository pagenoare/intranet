# -*- coding: utf-8 -*-

import json
import colander
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotFound, Response
from sqlalchemy.exc import IntegrityError

from intranet3.utils.views import ApiView
from intranet3 import models as m
from intranet3.schemas.sprint import BoardSchema
from intranet3.utils.decorators import has_perm
from intranet3 import helpers as h

from intranet3.views.scrum.sprint import FetchBugsMixin
from intranet3.models import Sprint
from intranet3.lib.scrum import SprintWrapper


@view_config(route_name='api_boards', renderer='json', permission="can_manage_sprint_boards")
class Boards(ApiView):

    def get(self):
        boards = [
            board.to_dict()
            for board in self.session.query(m.SprintBoard)
        ]
        return dict(
            boards=boards
        )

    def post(self):
        try:
            json_board = self.request.json_body
        except ValueError:
            raise HTTPBadRequest('Expect json')

        board_schema = BoardSchema()
        try:
            board = board_schema.deserialize(json_board)
        except colander.Invalid, e:
            errors = e.asdict()
            raise HTTPBadRequest(errors)

        board = m.SprintBoard(**board)
        self.session.add(board)

        try:
            self.session.flush()
        except IntegrityError:
            raise HTTPBadRequest('Board exists')

        return dict(
            id=board.id,
        )


@view_config(route_name='api_board', renderer='json', permission="can_manage_sprint_boards")
class Board(ApiView):

    def put(self):
        board_id = self.request.matchdict.get('board_id')
        board = m.SprintBoard.query.get(board_id)
        if not board:
            raise HTTPNotFound()

        try:
            json_body = self.request.json_body
        except ValueError:
            raise HTTPBadRequest('Expect json')

        schema = BoardSchema()
        try:
            board = schema.deserialize(json_body)
        except colander.Invalid, e:
            errors = e.asdict()
            raise HTTPBadRequest(errors)

        for key, value in board.iteritem():
            setattr(board, key, value)

        return HTTPOk("OK")

    def delete(self):
        board_id = self.request.matchdict.get('board_id')
        board = m.SprintBoard.query.get(board_id)
        if not board:
            raise HTTPNotFound()

        self.session.delete(board)

        return HTTPOk('OK')

@view_config(route_name='api_sprint_bugs', renderer='json', permission="can_manage_sprint_boards")
class Bugs(FetchBugsMixin, ApiView):
    def get(self):
        sprint_id = self.request.matchdict.get('sprint_id')
        sprint = Sprint.query.get(sprint_id)
        bugs = self._fetch_bugs(sprint)

        sw = SprintWrapper(sprint, bugs, self.request)
        response = json.dumps([
            bug.to_dict()
            for bug in sw.board.bugs
        ], default=h.json_dumps_default)

        return Response(
            response,
            content_type='application/json',
        )

