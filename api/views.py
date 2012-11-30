# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
import copy
import json
from datetime import datetime

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.conf import settings
from django.http import HttpResponse
import django.contrib.auth

import models

def _to_json(python_object):
    if isinstance(python_object, datetime):
        return python_object.strftime('%Y-%m-%dT%H:%M:%SZ')
    raise TypeError(u'%s %s is not JSON serializable' % (
        repr(python_object), type(python_object)
    ))

def render_to_json_response(dictionary, content_type="text/json", status=200):
    indent=None
    if True or settings.DEBUG:
        content_type = "text/javascript"
        indent = 2
    return HttpResponse(json.dumps(dictionary, indent=indent, default=_to_json),
                        content_type=content_type, status=status)

def get(obj):
    r = models.resolve(obj)
    if not r:
        r = {}
    return r

def set(user, query, update):
    r = models.set(query, update, user)
    return get(obj)

def log(obj):
    o = models.get(obj)
    query = {}
    if models.is_file(obj):
        query = {'_file': o['_id']}
    else:
        query = {'_work': o['_id']}
    revisions = []
    for rev in models.history.find(query).sort('date'):
        rev = models._cleanup(rev)
        revisions.append(rev)
    return {
        'revisions': revisions
    }

def login(request, username, password):
    user = django.contrib.auth.authenticate(username=username, password=password)
    if user and user.is_active:
        django.contrib.auth.login(request, user)
        return {
            'username': user.username,
        }
    return {
        'error': 'login failed'
    }

def api(request):
    if not request.body:
        keys = request.GET.keys()
        if keys:
            data = {'action': 'get', 'data': {}}
            for key in keys:
                data['data'][key] = request.GET[key]
        else:
            context = RequestContext(request, {'settings': settings})
            return render_to_response('index.html', context)
    else:
        data = json.loads(request.body)
    if data['action'] == 'login':
        response = login(request, data['data']['username'], data['data']['password'])
    elif data['action'] == 'get':
        response = get(data['data'])
    elif data['action'] == 'set':
        if request.user.is_anonymous():
            response = {'error': 'permission denied'}
        else:
            q = data['data']
            q['user'] = request.user.username
            r = models.set(**q)
            response = get(data['data']['query'])
    elif data['action'] == 'log':
        response = log(data['data'])
    return render_to_json_response(response)
