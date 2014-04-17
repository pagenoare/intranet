from os.path import dirname, join
from datetime import date

import json

from intranet3.testing import (
    IntranetWebTest,
    FactoryMixin,
)
from intranet3.models import TimeEntry, DBSession


ROOT_PATH = dirname(__file__)
SAMPLE_JIRA_REQUEST_PATH = join(ROOT_PATH, 'test_data/jira_request.json')


class JiraWebhookTestCase(FactoryMixin, IntranetWebTest):

    def test_add_time_entry_with_correct_ip(self):
        user = self.create_user()
        tracker = self.create_tracker('Hogarth Jira')
        project = self.create_project(
            name='project',
            user=user,
            tracker=tracker,
            project_selector='project'
        )
        self.add_creds(user, tracker, 'user_1')

        request_date = date(2014, 4, 17)

        with open(SAMPLE_JIRA_REQUEST_PATH, 'r') as f:
            sample_jira_request = f.read()

        resp = self.post_json(
            '/api/webhooks/jira',
            json.loads(sample_jira_request),
        )

        self.assertEqual(resp.status_code, 200)

        query = DBSession.query(TimeEntry).filter(TimeEntry.user_id==user.id)
        query = query.filter(TimeEntry.date==request_date)
        query = query.filter(TimeEntry.ticket_id=='ISSUE-1')
        query = query.filter(TimeEntry.project_id==project.id)
        entry = query.first()

        self.assertNotEqual(entry, None)
        self.assertEqual(entry.time, 2.0)
        self.assertEqual(entry.description, 'Test 1')

    def test_add_time_entry_with_wrong_ip(self):
        pass
