#!/usr/bin/env python
from datetime import datetime
import httplib
import json
import logging
import os.path

import jinja2
import webapp2
from google.appengine.api import users
from google.appengine.ext.webapp.util import login_required

import models
from models import Candidate
from config import bigquery
from config import PROJECT_ID

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('templates/index.html')
    response = bigquery.tables().list(
      projectId=PROJECT_ID, datasetId='reference').execute()
    
    self.response.write(template.render({
      'tables': [{
          'dataset': entry['tableReference']['datasetId'],
          'name': entry['tableReference']['tableId'],
      } for entry in response['tables']]}))

class ManageDevicesHandler(webapp2.RequestHandler):
  @login_required
  def get(self):
    user = users.get_current_user()
    self._show(user)

  def _show(self, user):
    data = {
      'user': user,
      'devices': [{
        'id': device.key.id(),
        'added': device.added.strftime('%c'),
        'make': device.make,
        'model': device.model,
        'zip': device.home_zip5,
      } for device in models.Device.by_owner(user)],
      'registration_id': Candidate.acquire_id(user)
    }
    template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
    self.response.write(template.render(data))

  def post(self):
    user = users.get_current_user()
    if user is None:
      self.abort(httplib.UNAUTHORIZED,
          'Must be logged in to manage devices.')
    action = self.request.get('action')
    if action == 'Add':
      models.Device.new(user, self.request).put()
    elif action == 'X':
      models.Device.key_from_id(user, self.request.get('id')).delete()
    else:
      self.abort(httplib.NOT_IMPLEMENTED, 
          detail=('Unsupported action %s' % action))
    self.redirect(self.request.route.build(
        self.request, [], {}))

class _JsonHandler(webapp2.RequestHandler):
  '''Generic JSON command handler.'''
  MAX_PAYLOAD_SIZE = 16 * 1024

  def post(self):
    if self.request.headers.get('Content-Type') != 'application/json':
      self.response.set_status(
          httplib.UNSUPPORTED_MEDIA_TYPE,
          message='Expected Content-Type: application/json')
      return
    if len(self.request.body) > self.MAX_PAYLOAD_SIZE:
      self.response.set_status(
          httplib.REQUEST_ENTITY_TOO_LARGE,
          message=('Max payload size (%d) exceeded' %
                        self.MAX_PAYLOAD_SIZE))
      return
    try:
      arg = json.loads(self.request.body)
    except ValueError, e:
      self.response.set_status(
          httplib.BAD_REQUEST,
          message='Could not parse body as json: ' + str(e))
      return
    self.response.headers['Content-Type'] = 'application/json'
    try:
      result = json.dumps(self.handle(arg))
    except Exception, e:
      result = self.json_error(e)
    self.response.out.write(result)

  def json_error(self, e):
    logging.warn('Handler Error: %s' % unicode(e))
    return json.dumps({'error': e.__class__.__name__,
                       'message': e.message})
    
  def handle(self, arg):
    raise NotImplementedError

class RegisterHandler(_JsonHandler):
  '''Handle the registration command.'''
  def handle(self, arg):
    device_id = arg.get('id', None)
    if not device_id:
      raise ValueError('id entry missing from argument')
    candidate = models.Candidate.get_by_device_id(device_id)
    if not candidate:
      raise KeyError('Id %s not valid' % device_id)
    candidate.register(arg)
    return {}

class RecordHandler(_JsonHandler):
  '''Handle the logging command.'''
  def handle(self, arg):
    device_id = arg.get('id', None)
    if not device_id:
      raise ValueError('id entry missing from argument')
    device = models.Device.get_by_device_id(device_id)
    if not device:
      raise KeyError('id %s not valid' % device_id)
    # Extract the UTC day from the timestamp in the record.
    ts = int(arg.get('ts', 0.0))
    day = datetime.utcfromtimestamp(ts)
    # Save the record using the streaming API.
    result = bigquery.tabledata().insertAll(
        projectId=PROJECT_ID,
        datasetId='logs',
        tableId='device_' + day.strftime("%Y%m%d"),
        body=dict(rows=[
            # Generate a suitable insert id.
            {'insertId': ('%s:%d' % (device_id, ts)),
             'json': arg}])).execute()
    if 'error' in result or result.get('insertErrors'):
      logging.error('Insert failed: ' + unicode(result))
    return {}

app = webapp2.WSGIApplication([
    webapp2.Route(r'/', handler=MainHandler, name='main'),
    webapp2.Route(r'/manage', handler=ManageDevicesHandler, name='manage'),
    webapp2.Route(r'/command/register',
        handler=RegisterHandler, name='register'),
    webapp2.Route(r'/command/record',
        handler=RecordHandler, name='record'),
], debug=True)