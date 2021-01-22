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
from urllib.parse import urlparse

from flask import Flask, request, Response
import redis
import jwt
import boto3
from botocore.exceptions import ClientError

application = Flask(__name__)


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

client = redis.Redis(
    host=os.environ['REDIS_HOST'],
    port=int(os.environ.get('REDIS_PORT', '6379')),
    charset="utf-8",
    decode_responses=True,
)

queue_name = os.environ['REDIS_REGISTER_QUEUE_KEY']
#TODO: extract credentials from the jwt token instead
access = os.environ['ACCESS']
secret = os.environ['SECRET']
env_host=os.environ['HOST']


def upload_file(host, file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
    
   
    # Upload the file
    s3_client = boto3.client('s3',aws_access_key_id= access, aws_secret_access_key= secret, endpoint_url=host,)
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.exception(e)
        return False
    return True
# This is an experemental function that could be moved or replaced by lookup for buckets instead
def lookup_objects(host, access_key, secret_key, bucketname, pref):

    
    s3 = boto3.resource('s3',aws_access_key_id=access_key, aws_secret_access_key=secret_key, endpoint_url=host,)
    bucket=s3.Bucket(bucketname)

    for obj in bucket.objects.filter():
        if pref in obj.key:
            return True
        else: 
            return False

@application.route('/userinfo', methods=['GET'])
def userinfo():
    # At the current state this function creates dummy objects and name them based on a prefix from jwt
    request.get_data()
    auth_header = request.headers['Authorization'] 
    if not auth_header.startswith('Bearer '): 
        raise Exception
    token = auth_header[len('Bearer '):]
    encode_token = jwt.decode(token, verify=False, algorithms=['RS256'])
    prefix = encode_token['pct_claims']['aud']

    if lookup_objects(env_host, access, secret, 'test_stage_out', prefix) :
        response = 'An Object with the prefix %s already exists' % prefix

    else:
        upload_file(env_host, 'image.tif', 'test_stage_out', '%s.tif' % prefix)
        upload_file(env_host, 'stac.json', 'test_stage_out', '%s.json' % prefix)

        response = 'created objects with the prefix: %s , in "test_stage_out" bucket' % prefix

    return response

@application.route('/register', methods=['POST'])
def register():

    request.get_data()

    auth_header = request.headers['Authorization'] 
    if not auth_header.startswith('Bearer '): 
        raise Exception
    token = auth_header[len('Bearer '):]
    encode_token = jwt.decode(token, verify=False, algorithms=['RS256'])
    prefix = encode_token['pct_claims']['aud']
    try:
        request_body = request.get_json()
    except Exception :
        raise Exception

    #TODO json schema check

    parsed_url = urlparse(request_body["url"])
    url = parsed_url.netloc + parsed_url.path 

    #TODO: presumably th client should pass a stac URL
    client.lpush(queue_name, url)
    response = "successfully added item %s to the redis queue" %  url
    return response

if __name__ == "__main__":
    application.run()