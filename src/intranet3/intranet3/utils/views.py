import datetime
import calendar
import json
import os

from pyramid.httpexceptions import HTTPException, HTTPMethodNotAllowed, HTTPBadRequest, HTTPNotFound
from pyramid.i18n import TranslationStringFactory, get_localizer
from netaddr import AddrFormatError, IPAddress, IPNetwork, IPRange

from intranet3 import models
from intranet3.log import INFO_LOG
from intranet3.models import DBSession

LOG = INFO_LOG(__name__)


class View(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.flash = lambda message, klass='': request.session.flash((klass, message))
        self.settings = self.request.registry.settings # shortcut

        tsf = TranslationStringFactory('intranet3')
        localizer = get_localizer(request)

        def _(string, **kwargs):
            return localizer.translate(tsf(string, mapping=kwargs))
        self._ = _

        # inside view cache, put here objects that will be used further in processing
        # for example after validation client object in protect() method the same object will be used in tmpl_ctx or main part of view (get method)
        self.v = {}


def _check_ip(remote_addr, office_ip):
    """
    Checks if `remote_addr` belongs to `office_ip`

        Keyword arguments:
        remote_addr -- user IPAddress
        office_ip -- office IPAddress or IPNetwork

        `office_ip`:
        127.0.0.1/26 -- IPNetwork
        127.0.0.1-127.0.1.255 -- IPAddress range
        127.0.0.1 -- IPAddress
    """
    try:
        remote_addr = IPAddress(remote_addr)

        if '-' in office_ip:
            start, end = office_ip.split('-')
            return remote_addr in IPRange(start, end)
        elif '/' in office_ip:
            return remote_addr in IPNetwork(office_ip)
        else:
            return remote_addr == IPAddress(office_ip)
    except AddrFormatError:
        return False


class BaseView(View):
    def _note_presence(self):
        """
        Check if request IP equals database-stored office IP.
        If it does, add a presence entry.
        If no office IP was configured, this method does nothing.
        Adds a presence entry to the datastore
        """
        office_ips = models.ApplicationConfig.get_office_ip()
        if not office_ips: # not yet configured
            return
        current_ip = self.request.headers.get('X-Forwarded-For', '127.0.0.1')
        for office_ip in office_ips:
            if _check_ip(current_ip, office_ip):
                presence = models.PresenceEntry(url=self.request.url, user_id=self.request.user.id)
                DBSession.add(presence)
                LOG(u'Noticed presence of user %s (%s)' % (self.request.user.email, current_ip))
                break
        else:
            LOG(u'User %s presence ignored (%s)' % (self.request.user.email, current_ip))

    def protect(self):
        """
        Override this method to check condtition and rise HTTPForbidden or not
        """

    def tmpl_ctx(self):
        return {}

    def dispatch(self):
        if self.request.method == 'GET':
            return self.get()
        elif self.request.method == 'POST':
            return self.post()
        else:
            raise HTTPNotFound()

    def __call__(self):
        self.protect()
        self._note_presence()
        self.request.tmpl_ctx.update(self.tmpl_ctx())
        return self.dispatch()

    def get(self):
        raise HTTPNotFound()

    def post(self):
        raise HTTPNotFound()


class ApiView(BaseView):

    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self, context, request):
        def _response_exception(request, response):
            try:
                e = response.exception
            except AttributeError:
                return response

            if isinstance(e, HTTPException):
                response.content_type = "application/json"
                response.body = json.dumps({'message': e.message})

            return response
        request.add_response_callback(_response_exception)

        super(ApiView, self).__init__(context, request)

        self.flash = lambda message, klass='': None # We don't need flash messages. So do nothing

    def _note_presence(self):
        """
        No presence checking for calls to API
        """
        pass

    def dispatch(self):
        if self.request.method.lower() in self.http_method_names:
            handler = getattr(self, self.request.method.lower(), self.http_not_allowed_method)
        else:
            handler = self.http_not_allowed_method

        return handler()

    def http_not_allowed_method(self):
        raise HTTPMethodNotAllowed("Method Not Allowed")


class CronView(View):
    def __call__(self):
        return self.action()

    def action(self):
        raise HTTPNotFound()


class TaskView(CronView):
    pass


class MonthMixin(object):
    """
    Mixin for creating start and end date of month from GET month parameter('%m.%y')
    """
    def _get_month(self):
        try:
            month = self.request.GET.get('month')
            month, year = month.split('.')
            month, year = int(month), int(year)
            start_date = datetime.date(year, month, 1)
        except ValueError:
            raise HTTPBadRequest()
        else:
            day_of_week, days_in_month = calendar.monthrange(year, month)
            end_date = datetime.date(year, month, days_in_month)
            return start_date, end_date

