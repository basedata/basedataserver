# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from datetime import datetime
import base64

from pymongo import Connection, ASCENDING
from django.conf import settings

import utils


connection = Connection()

db = connection[settings.MONGODB]
files = db.files
works = db.works
history = db.history

files.create_index([('sha1', ASCENDING),])
files.create_index([('md5', ASCENDING),])
files.create_index([('oshash', ASCENDING),])
files.create_index([('_work', ASCENDING),])

works.create_index([('isbn', ASCENDING),])
works.create_index([('openlibrary', ASCENDING),])


def is_file_key(key, query=False):
    keys = ['sha1', 'md5', 'oshash']
    if not query:
        keys = keys + ['size', 'extension']
    return key in keys

def is_file(obj):
    for key in obj:
        if is_file_key(key, True):
            return True
    return False

def get_or_create(obj):
    table = getattr(db, is_file(obj) and 'files' or 'works')
    o = table.find_one(obj)
    if not o:
        o = obj
        o['_id'] = table.save(obj)
    return o

def get(obj):
    if is_file(obj):
        if 'md5' in obj:
            obj['md5'] = utils.normalize_md5(obj['md5'])
        if 'sha1' in obj:
            obj['sha1'] = utils.normalize_sha1(obj['sha1'])
        o = files.find_one(obj)
    else:
        o = works.find_one(obj)
    return o

def _cleanup(obj):
    for key in obj.keys():
        if key.startswith('_'):
            del obj[key]
    return obj

def resolve(obj):
    r = get(obj)
    if r:
        if '_work' in r:
            work = works.find_one({'_id': r['_work']})
            r['work'] = _cleanup(work)
        else:
            r['files'] = []
            for f in files.find({'_work': r['_id']}):
                r['files'].append(_cleanup(f))
        r = _cleanup(r)
    return r

def update_key(obj, key, value):
    if isinstance(value, dict):
        if not key in obj or not isinstance(obj[key], dict):
            obj[key] = {}
        for k in value:
            update_key(obj[key], k, value[k])
    else:
        if value == None:
            if key in obj:
                del obj[key]
        else:
            obj[key] = value

def set(query, update, user=None, description=''):
    table = getattr(db, is_file(query) and 'files' or 'works')
    o = get_or_create(query)
    w = None
    o_is_file = is_file(query)
    updated = False
    for key in update:
        if key.startswith('_') or key in ('id', 'work', 'files'):
            continue
        value = update[key]
        if key == 'md5':
            value = utils.normalize_md5(value)
        elif key == 'sha1':
            value = utils.normalize_sha1(value)
        elif key == 'oshash':
            value = utils.normalize_oshash(value)
        elif key == 'isbn':
            if isinstance(value, list):
                value = filter(None, [utils.check_isbn(i) for i in value])
            else:
                value = utils.check_isbn(value)
        elif key == 'openlibrary':
            value = utils.check_openlibrary(value)
        if o_is_file:
            if not is_file_key(key):
                if not w:
                    if not '_work' in o:
                        if not isinstance(value, list):
                           _value = [value]
                        else:
                           _value = value
                        for v in _value:
                            obj = {}
                            obj[key] = v
                            w = get(obj)
                            if w: break
                        if not w:
                            w = get_or_create(obj)

                        o['_work'] = w['_id']
                        db.files.save(o)
                    else:
                        w = db.works.find_one({'_id': o['_work']})
                #fixme: enforce uniqueness for ids
                update_key(w, key, value)
            else:
                update_key(o, key, value)
                updated = True
        else:
            if is_file_key(key):
                raise Exception, 'can not set file key on work'
            update_key(o, key, value)
            updated = True
    if w:
        db.works.save(w)
        if user:
            log(user, w, description)
    if updated:
        table.save(o)
        if user:
            log(user, o, description)
    return o

def log(user, obj, description=''):
    d = {
        'user': user,
        'date': datetime.now(),
    }
    if description:
        d['description'] = description
    if is_file(obj):
        f = files.find_one(obj)
        d['_file'] = f['_id']
        d['data'] = resolve(f)
    else:
        w = works.find_one(obj)
        d['_work'] = w['_id']
        d['data'] = resolve(w)
    history.save(d)

