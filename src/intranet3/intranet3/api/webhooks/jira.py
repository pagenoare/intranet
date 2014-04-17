import datetime
from pyramid.view import view_config
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.response import Response

from intranet3.models import DBSession, Tracker, TrackerCredentials
from intranet3.models.project import SelectorMapping
from intranet3.utils.views import ApiView
from intranet3.utils.timeentry import add_time
from intranet3.log import DEBUG_LOG

DEBUG = DEBUG_LOG(__name__)


@view_config(route_name='webhook_jira', renderer='json', permission=NO_PERMISSION_REQUIRED)
class JiraWebhookHandler(ApiView):

    def post(self):
        self.data = self.request.json_body
        query = Tracker.query.filter(Tracker.name == 'Hogarth Jira') # TODO this one should be more generic
        self.tracker = query.first()
        projects_mapping = SelectorMapping(self.tracker)
        required_master_keys = ('user', 'changelog', 'issue', 'timestamp')

        for key in required_master_keys:
            if key not in self.data:
                DEBUG('Key {} couldnt be found'.format(key))
                return Response(status=400)

        if 'name' not in self.data['user']:
            DEBUG('Key name/user couldnt be found')
            return Response(status=400)

        if 'fields' not in self.data['issue']:
            DEBUG('Key issue/fields couldnt be found')
            return Response(status=400)

        if 'project' not in self.data['issue']['fields']:
            DEBUG('Key issue/fields/project couldnt be found')
            return Response(status=400)

        date = datetime.datetime.fromtimestamp(self.data['timestamp'] / 1000)
        user = self._get_user(self.data['user']['name'])
        if not user:
            DEBUG('User couldnt be found')
            return Response(status=400)

        bug_id = self.data['issue'].get('key')
        if not bug_id:
            DEBUG('Bug ID couldnt be parsed')
            return Response(status=400)

        project_id = projects_mapping.by_project.get(
            self.data['issue']['fields']['project'].get('name')
        )
        if not project_id:
            DEBUG('Project couldnt be found')
            return Response(status=400)

        hours = self._get_hours()
        if not hours:
            DEBUG('Hours couldnt be parsed')
            return Response(status=400)

        subject = self.data['issue']['fields'].get('summary')
        if not subject:
            DEBUG('Subject couldnt be parsed')
            return Response(status=400)

        entry = add_time(user.id, date, bug_id, project_id, hours, subject)
        if not entry:
            DEBUG('Error on creating TimeEntry')
            return Response(status=400)

        DBSession.add(entry)
        return Response(status=200)

    def _get_hours(self):
        try:
            timespent = sum([
                int(changelog['to'])
                for changelog in self.data['changelog'].get('items', [])
                if changelog.get('field') == 'timespent'
            ])
        except ValueError:
            return

        # JIRA sends us time in secs, so we need to reformat it to hours
        return float(timespent) / (60 * 60)

    def _get_user(self, username):
        logins_mapping = TrackerCredentials.get_logins_mapping(self.tracker)
        return logins_mapping.get(username)
