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

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


class CRUD(object):

    supported_ops = ["create", "update", "get", "delete", "list"]

    def __init__(self, dynamodb_table, required_attributes,
                 supported_ops=None):
        self._table = dynamodb_table
        self._required = required_attributes
        self._supported_ops = supported_ops or self.supported_ops

    def _check_required(self, item, response):
        missing = self._required - set(item.keys())
        if len(missing) > 0:
            response['status'] = 'error'
            response['message'] = 'Missing required attributes: {}'.format(
                list(missing))
            return False
        return True

    def _list(self, item, response):
        items = self._table.scan()
        response['data'] = items['Items']

    def _create(self, item, response):
        item['id'] = str(uuid.uuid4())
        item['created_at'] = int(time.time() * 1000)
        item['modified_at'] = item['created']
        if self._check_required(item, response):
            self._table.put_item(Item=item)
            response['data'] = item

    def _update(self, item, response):
        item['modified_at'] = int(time.time() * 1000)
        if self._check_required(item, response):
            self._table.put_item(Item=item)
            response['data'] = item

    def _delete(self, item, response):
        id = item.get('id')
        if id is None:
            response['status'] = 'error'
            response['message'] = 'delete requires an id'
        else:
            response['data'] = self._table.delete_item(Key={'id': id})

    def _get(self, item, response):
        id = item.get('id')
        if id is None:
            response['status'] = 'error'
            response['message'] = 'get requires an id'
        else:
            response['data'] = self._table.get_item(Key={'id': id})

    def handler(self, item, operation):
        response = {'status': 'success'}
        operation = operation.lower()
        if not operation:
            response['status'] = 'error'
            response['message'] = 'NoOperationSupplied'
        elif operation not in self._supported_operations:
            response['status'] = 'error'
            response['message'] = 'UnsupportedOperation: {}'.format(operation)
        elif operation == 'list':
            self._list(item, response)
        elif operation == 'get':
            self._get(item, response)
        elif operation == 'create':
            self._create(item, response)
        elif operation == 'update':
            self._update(item, response)
        elif operation == 'delete':
            self._delete(item, response)
        return response
