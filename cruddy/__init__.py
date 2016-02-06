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

import os
import logging
import decimal
import base64
import copy
import inspect

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from cruddy.prototype import PrototypeHandler
from cruddy.response import CRUDResponse

__version__ = open(os.path.join(os.path.dirname(__file__),
                                '_version')).read().strip()

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


class CRUD(object):

    SupportedOps = ["create", "update", "get", "delete", "bulk_delete",
                    "list", "search", "increment_counter",
                    "describe", "ping"]

    def __init__(self, **kwargs):
        """
        Create a new CRUD handler.  The CRUD handler accepts the following
        parameters:

        * table_name - name of the backing DynamoDB table (required)
        * profile_name - name of the AWS credential profile to use when
          creating the boto3 Session
        * region_name - name of the AWS region to use when creating the
          boto3 Session
        * prototype - a dictionary of name/value pairs that will be used to
          initialize newly created items
        * supported_ops - a list of operations supported by the CRUD handler
          (choices are list, get, create, update, delete, search,
          increment_counter, describe, help, ping)
        * encrypted_attributes - a list of tuples where the first item in the
          tuple is the name of the attribute that should be encrypted and the
          second item in the tuple is the KMS master key ID to use for
          encrypting/decrypting the value
        * debug - if not False this will cause the raw_response to be left
          in the response dictionary
        """
        self.table_name = kwargs['table_name']
        profile_name = kwargs.get('profile_name')
        region_name = kwargs.get('region_name')
        placebo = kwargs.get('placebo')
        placebo_dir = kwargs.get('placebo_dir')
        placebo_mode = kwargs.get('placebo_mode', 'record')
        self.prototype = kwargs.get('prototype', dict())
        self._prototype_handler = PrototypeHandler(self.prototype)
        self.supported_ops = kwargs.get('supported_ops', self.SupportedOps)
        self.supported_ops.append('describe')
        self.encrypted_attributes = kwargs.get('encrypted_attributes', list())
        session = boto3.Session(profile_name=profile_name,
                                region_name=region_name)
        if placebo and placebo_dir:
            self.pill = placebo.attach(session, placebo_dir, debug=True)
            if placebo_mode == 'record':
                self.pill.record()
            else:
                self.pill.playback()
        else:
            self.pill = None
        ddb_resource = session.resource('dynamodb')
        self.table = ddb_resource.Table(self.table_name)
        self._indexes = {}
        self._analyze_table()
        self._debug = kwargs.get('debug', False)
        if self.encrypted_attributes:
            self._kms_client = session.client('kms')
        else:
            self._kms_client = None

    def _analyze_table(self):
        # First check the Key Schema
        if len(self.table.key_schema) != 1:
            LOG.info('cruddy does not support RANGE keys')
        else:
            self._indexes[self.table.key_schema[0]['AttributeName']] = None
        # Now process any GSI's
        if self.table.global_secondary_indexes:
            for gsi in self.table.global_secondary_indexes:
                # find HASH of GSI, that's all we support for now
                # if the GSI has a RANGE, we ignore it for now
                if len(gsi['KeySchema']) == 1:
                    gsi_hash = gsi['KeySchema'][0]['AttributeName']
                    self._indexes[gsi_hash] = gsi['IndexName']

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

    def ping(self, **kwargs):
        """
        A no-op method that simply returns a successful response.
        """
        response = self._new_response()
        return response

    def describe(self, **kwargs):
        """
        Returns descriptive information about this cruddy handler and the
        methods supported by it.
        """
        response = self._new_response()
        description = {
            'cruddy_version': __version__,
            'table_name': self.table_name,
            'supported_operations': copy.copy(self.supported_ops),
            'prototype': copy.deepcopy(self.prototype),
            'operations': {}
        }
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if not name.startswith('_'):
                argspec = inspect.getargspec(method)
                if argspec.defaults is None:
                    defaults = None
                else:
                    defaults = list(argspec.defaults)
                method_info = {
                    'docs': inspect.getdoc(method),
                    'argspec': {
                        'args': argspec.args,
                        'varargs': argspec.varargs,
                        'keywords': argspec.keywords,
                        'defaults': defaults
                    }
                }
                description['operations'][name] = method_info
        response.data = description
        return response

    def search(self, query, **kwargs):
        """
        Cruddy provides a limited but useful interface to search GSI indexes in
        DynamoDB with the following limitations (hopefully some of these will
        be expanded or eliminated in the future.

        * The GSI must be configured with a only HASH and not a RANGE.
        * The only operation supported in the query is equality

        To use the ``search`` operation you must pass in a query string of this
        form:

            <attribute_name>=<value>

        As stated above, the only operation currently supported is equality (=)
        but other operations will be added over time.  Also, the
        ``attribute_name`` must be an attribute which is configured as the
        ``HASH`` of a GSI in the DynamoDB table.  If all of the above
        conditions are met, the ``query`` operation will return a list
        (possibly empty) of all items matching the query and the ``status`` of
        the response will be ``success``.  Otherwise, the ``status`` will be
        ``error`` and the ``error_type`` and ``error_message`` will provide
        further information about the error.
        """
        response = self._new_response()
        if self._check_supported_op('search', response):
            if '=' not in query:
                response.status = 'error'
                response.error_type = 'InvalidQuery'
                msg = 'Only the = operation is supported'
                response.error_message = msg
            else:
                key, value = query.split('=')
                if key not in self._indexes:
                    response.status = 'error'
                    response.error_type = 'InvalidQuery'
                    msg = 'Attribute {} is not indexed'.format(key)
                    response.error_message = msg
                else:
                    params = {'KeyConditionExpression': Key(key).eq(value)}
                    index_name = self._indexes[key]
                    if index_name:
                        params['IndexName'] = index_name
                    pe = kwargs.get('projection_expression')
                    if pe:
                        params['ProjectionExpression'] = pe
                    self._call_ddb_method(self.table.query,
                                          params, response)
                    if response.status == 'success':
                        response.data = self._replace_decimals(
                            response.raw_response['Items'])
        response.prepare()
        return response

    def list(self, **kwargs):
        """
        Returns a list of items in the database.  Encrypted attributes are not
        decrypted when listing items.
        """
        response = self._new_response()
        if self._check_supported_op('list', response):
            self._call_ddb_method(self.table.scan, {}, response)
            if response.status == 'success':
                response.data = self._replace_decimals(
                    response.raw_response['Items'])
        response.prepare()
        return response

    def get(self, id, decrypt=False, id_name='id', **kwargs):
        """
        Returns the item corresponding to ``id``.  If the ``decrypt`` param is
        not False (the default) any encrypted attributes in the item will be
        decrypted before the item is returned.  If not, the encrypted
        attributes will contain the encrypted value.

        """
        response = self._new_response()
        if self._check_supported_op('get', response):
            if id is None:
                response.status = 'error'
                response.error_type = 'IDRequired'
                response.error_message = 'Get requires an id'
            else:
                params = {'Key': {id_name: id},
                          'ConsistentRead': True}
                self._call_ddb_method(self.table.get_item,
                                      params, response)
                if response.status == 'success':
                    if 'Item' in response.raw_response:
                        item = response.raw_response['Item']
                        if decrypt:
                            self._decrypt(item)
                        response.data = self._replace_decimals(item)
                    else:
                        response.status = 'error'
                        response.error_type = 'NotFound'
                        msg = 'item ({}) not found'.format(id)
                        response.error_message = msg
        response.prepare()
        return response

    def create(self, item, **kwargs):
        """
        Creates a new item.  You pass in an item containing initial values.
        Any attribute names defined in ``prototype`` that are missing from the
        item will be added using the default value defined in ``prototype``.
        """
        response = self._new_response()
        if self._prototype_handler.check(item, 'create', response):
            self._encrypt(item)
            params = {'Item': item}
            self._call_ddb_method(self.table.put_item,
                                  params, response)
            if response.status == 'success':
                response.data = item
        response.prepare()
        return response

    def update(self, item, encrypt=True, **kwargs):
        """
        Updates the item based on the current values of the dictionary passed
        in.
        """
        response = self._new_response()
        if self._check_supported_op('update', response):
            if self._prototype_handler.check(item, 'update', response):
                if encrypt:
                    self._encrypt(item)
                params = {'Item': item}
                self._call_ddb_method(self.table.put_item,
                                      params, response)
                if response.status == 'success':
                    response.data = item
        response.prepare()
        return response

    def increment_counter(self, id, counter_name, increment=1,
                          id_name='id', **kwargs):
        """
        Atomically increments a counter attribute in the item identified by
        ``id``.  You must specify the name of the attribute as ``counter_name``
        and, optionally, the ``increment`` which defaults to ``1``.
        """
        response = self._new_response()
        if self._check_supported_op('increment_counter', response):
            params = {
                'Key': {id_name: id},
                'UpdateExpression': 'set #ctr = #ctr + :val',
                'ExpressionAttributeNames': {"#ctr": counter_name},
                'ExpressionAttributeValues': {
                    ':val': decimal.Decimal(increment)},
                'ReturnValues': 'UPDATED_NEW'
            }
            self._call_ddb_method(self.table.update_item, params, response)
            if response.status == 'success':
                if 'Attributes' in response.raw_response:
                    self._replace_decimals(response.raw_response)
                    attr = response.raw_response['Attributes'][counter_name]
                    response.data = attr
        response.prepare()
        return response

    def delete(self, id, id_name='id', **kwargs):
        """
        Deletes the item corresponding to ``id``.
        """
        response = self._new_response()
        if self._check_supported_op('delete', response):
            params = {'Key': {id_name: id}}
            self._call_ddb_method(self.table.delete_item, params, response)
            response.data = 'true'
        response.prepare()
        return response

    def bulk_delete(self, query, **kwargs):
        """
        Perform a search and delete all items that match.
        """
        response = self._new_response()
        if self._check_supported_op('search', response):
            n = 0
            pe = 'id'
            response = self.search(query, projection_expression=pe, **kwargs)
            while response.status == 'success' and response.data:
                for item in response.data:
                    delete_response = self.delete(item['id'])
                    if response.status != 'success':
                        response = delete_response
                        break
                    n += 1
                response = self.search(
                    query, projection_expression=pe, **kwargs)
            if response.status == 'success':
                response.data = {'deleted': n}
        return response

    def handler(self, operation=None, **kwargs):
        """
        In addition to the methods described above, cruddy also provides a
        generic handler interface.  This is mainly useful when you want to wrap
        a cruddy handler in a Lambda function and then call that Lambda
        function to access the CRUD capabilities.

        To call the handler, you simply put all necessary parameters into a
        Python dictionary and then call the handler with that dict.

        ```
        params = {
            'operation': 'create',
            'item': {'foo': 'bar', 'fie': 'baz'}
        }
        response = crud.handler(**params)
        ```
        """
        response = self._new_response()
        if operation is None:
            response.status = 'error'
            response.error_type = 'MissingOperation'
            response.error_message = 'You must pass an operation'
            return response
        operation = operation.lower()
        self._check_supported_op(operation, response)
        if response.status == 'success':
            method = getattr(self, operation, None)
            if callable(method):
                response = method(**kwargs)
            else:
                response.status == 'error'
                response.error_type = 'NotImplemented'
                msg = 'Operation: {} is not implemented'.format(operation)
                response.error_message = msg
        return response
