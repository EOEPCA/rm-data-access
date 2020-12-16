#!/usr/bin/env python
#------------------------------------------------------------------------------
#
# Project: prism view server
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH <https://eox.at>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#-----------------------------------------------------------------------------

import os
import logging
import logging.config
import json

from flask import Flask, request, Response
import jwt
import boto3

application = Flask(__name__)
application.secret_key = "jose"  # Make this long, random, and secret in a real app!


logger = logging.getLogger(__name__)

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s: %(message)s',
        },
        'verbose': {
            'format': '[%(asctime)s][%(module)s] %(levelname)s: %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
})

access = '80658bec0ce34880a9bbc3f3f50ca60b'
secret = '9069592f9b314a52b26915e35fbef581'


def add_object(access_key,secret_key, bucketname, prefix):
    host = 'https://cf2.cloudferro.com:8080'
    s3 = boto3.resource('s3',aws_access_key_id=access_key, aws_secret_access_key=secret_key, endpoint_url=host,)

    bucket =s3.Bucket(bucketname)

    bucket.put_object(Key=prefix)

def lookup_objects(access_key, secret_key, bucketname, pref):
    host = 'https://cf2.cloudferro.com:8080'
    s3 = boto3.resource('s3',aws_access_key_id=access_key, aws_secret_access_key=secret_key, endpoint_url=host,)

    bucket=s3.Bucket(bucketname)
    for obj in bucket.objects.filter():
        if pref == obj.key:
            return True
        else: 
            return False

@application.route('/userinfo', methods=['GET'])
def store():
    request.get_data()
    encode_token = jwt.decode(request.headers['jwt-token'], verify=False, algorithms=['RS256'])
    prefix = encode_token['pct_claims']['aud']

    if lookup_objects(access, secret, 'test_stage_out', prefix) :
        response = 'An Object with the prefix %s already exists' % prefix
    else:
        try:
            add_object(access, secret, 'test_stage_out', prefix)
            response = 'created object %s in test_stage_out bucket' % prefix
        except Exception as e:
            response = e

    return response

@application.route('/register', methods=['POST'])
def register():
    request.get_data()
    return request.data

if __name__ == "__main__":
    application.run()