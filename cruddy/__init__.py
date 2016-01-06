# Copyright (c) 2016 CloudNative, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import uuid
import time
import decimal
import base64

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


class CRUDResponse(object):

    def __init__(self, debug=False):
        self._debug = debug
        self.status = 'success'
        self.data = None
        self.error_type = None
        self.error_code = None
        self.error_message = None
        self.raw_response = None
        self.metadata = None

    @property
    def is_successful(self):
        return self.status == 'success'

    def prepare(self):
        if self.status == 'success':
            if self.raw_response:
                if not self._debug:
                    md = self.raw_response['ResponseMetadata']
                    self.metadata = md
                    self.raw_response = None


class CRUD(object):

    SupportedOps = ["create", "update", "get", "delete", "list"]

    def __init__(self, **kwargs):
        """
        Create a new CRUD handler.  The CRUD handler accepts the following
        parameters:

        * table_name - name of the backing DynamoDB table (required)
        * profile_name - name of the AWS credential profile to use when
          creating the boto3 Session
        * region_name - name of the AWS region to use when creating the
          boto3 Session
        * required_attributes - a list of attribute names that the item is
          required to have or else an error will be returned
        * supported_ops - a list of operations supported by the CRUD handler
          (choices are list, get, create, update, delete)
        * encrypted_attributes - a list of tuples where the first item in the
          tuple is the name of the attribute that should be encrypted and the
          second item in the tuple is the KMS master key ID to use for
          encrypting/decrypting the value
        * debug - if not False this will cause the raw_response to be left
          in the response dictionary
        """
        table_name = kwargs['table_name']
        profile_name = kwargs.get('profile_name')
        region_name = kwargs.get('region_name')
        placebo = kwargs.get('placebo')
        placebo_dir = kwargs.get('placebo_dir')
        self.required_attributes = kwargs.get('required_attributes', list())
        self.supported_ops = kwargs.get('supported_ops', self.SupportedOps)
        self.encrypted_attributes = kwargs.get('encrypted_attributes', list())
        session = boto3.Session(profile_name=profile_name,
                                region_name=region_name)
        if placebo and placebo_dir:
            self.pill = placebo.attach(session, placebo_dir, debug=True)
        else:
            self.pill = None
        ddb_resource = session.resource('dynamodb')
        self.table = ddb_resource.Table(table_name)
        self._debug = kwargs.get('debug', False)
        if self.encrypted_attributes:
            self._kms_client = session.client('kms')
        else:
            self._kms_client = None

    # Because the Boto3 DynamoDB client turns all numeric types into Decimals
    # (which is actually the right thing to do) we need to convert those
    # Decimal values back into integers or floats before serializing to JSON.

    def _replace_decimals(self, obj):
        if isinstance(obj, list):
            for i in xrange(len(obj)):
                obj[i] = self._replace_decimals(obj[i])
            return obj
        elif isinstance(obj, dict):
            for k in obj.iterkeys():
                obj[k] = self._replace_decimals(obj[k])
            return obj
        elif isinstance(obj, decimal.Decimal):
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        else:
            return obj

    def _encrypt(self, item):
        for encrypted_attr, master_key_id in self.encrypted_attributes:
            if encrypted_attr in item:
                response = self._kms_client.encrypt(
                    KeyId=master_key_id,
                    Plaintext=item[encrypted_attr])
                blob = response['CiphertextBlob']
                item[encrypted_attr] = base64.b64encode(blob)

    def _decrypt(self, item):
        for encrypted_attr, master_key_id in self.encrypted_attributes:
            if encrypted_attr in item:
                response = self._kms_client.decrypt(
                    CiphertextBlob=base64.b64decode(item[encrypted_attr]))
                item[encrypted_attr] = response['Plaintext']

    def _check_required(self, item, response):
        missing = set(self.required_attributes) - set(item.keys())
        if len(missing) > 0:
            response.status = 'error'
            response.error_type = 'MissingRequiredAttributes'
            response.error_message = 'Missing required attributes: {}'.format(
                list(missing))
            return False
        return True

    def _check_supported_op(self, op_name, response):
        if op_name not in self.supported_ops:
            response.status = 'error'
            response.error_type = 'UnsupportedOperation'
            response.error_message = 'Unsupported operation: {}'.format(
                op_name)
            return False
        return True

    def _call_ddb_method(self, method, kwargs, response):
        try:
            response.raw_response = method(**kwargs)
        except ClientError as e:
            LOG.debug(e)
            response.status = 'error'
            response.error_message = e.response['Error'].get('Message')
            response.error_code = e.response['Error'].get('Code')
            response.error_type = e.response['Error'].get('Type')
        except Exception as e:
            response.status = 'error'
            response.error_type = e.__class__.__name__
            response.error_code = None
            response.error_message = str(e)

    def _new_response(self):
        return CRUDResponse(self._debug)

    def _get_ts(self):
        return int(time.time() * 1000)

    def list(self):
        response = self._new_response()
        if self._check_supported_op('list', response):
            self._call_ddb_method(self.table.scan, {}, response)
            if response.status == 'success':
                response.data = self._replace_decimals(
                    response.raw_response['Items'])
        response.prepare()
        return response

    def get(self, id, decrypt=False):
        response = self._new_response()
        if self._check_supported_op('list', response):
            if id is None:
                response.status = 'error'
                response.error_type = 'IDRequired'
                response.error_message = 'Get requires an id'
            else:
                params = {'Key': {'id': id},
                          'ConsistentRead': True}
                self._call_ddb_method(self.table.get_item, params, response)
                if response.status == 'success':
                    item = response.raw_response['Item']
                    if decrypt:
                        self._decrypt(item)
                    response.data = self._replace_decimals(item)
        response.prepare()
        return response

    def create(self, item):
        response = self._new_response()
        if self._check_supported_op('create', response):
            item['id'] = str(uuid.uuid4())
            item['created_at'] = self._get_ts()
            item['modified_at'] = item['created_at']
            if self._check_required(item, response):
                self._encrypt(item)
                params = {'Item': item}
                self._call_ddb_method(self.table.put_item, params, response)
                if response.status == 'success':
                    response.data = item
        response.prepare()
        return response

    def update(self, item):
        response = self._new_response()
        if self._check_supported_op('update', response):
            item['modified_at'] = self._get_ts()
            if self._check_required(item, response):
                self._encrypt(item)
                params = {'Item': item}
                self._call_ddb_method(self.table.put_item, params, response)
                if response.status == 'success':
                    response.data = item
        response.prepare()
        return response

    def delete(self, id):
        response = self._new_response()
        if self._check_supported_op('delete', response):
            if id is None:
                response.status = 'error'
                response.error_type = 'IDRequired'
                response.error_message = 'Delete requires an id'
            else:
                params = {'Key': {'id': id}}
                self._call_ddb_method(self.table.delete_item, params, response)
        response.prepare()
        return response

    def handler(self, item, operation):
        operation = operation.lower()
        if operation == 'list':
            response = self.list()
        elif operation == 'get':
            response = self.get(item['id'])
        elif operation == 'create':
            response = self.create(item)
        elif operation == 'update':
            response = self.update(item)
        elif operation == 'delete':
            response = self.delete(item['id'])
        return response
