# Copyright (c) 2016 CloudNative, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import unittest
import re

from cruddy.prototype import PrototypeHandler
from cruddy.response import CRUDResponse


class TestPrototype(unittest.TestCase):

    def setUp(self):
        self.uuid_re = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

    def tearDown(self):
        pass

    def test_no_prototype(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({})
        item = {'foo': 'bar'}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)

    def test_int_type_value_wrong_type(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': int})
        item = {'foo': 'bar'}
        result = prototype.check(item, 'create', response)
        self.assertFalse(result)
        self.assertEqual(response.status, 'error')
        self.assertEqual(response.error_type, 'InvalidType')

    def test_int_type_value_right_type(self):
        prototype = PrototypeHandler({'foo': int})
        response = CRUDResponse()
        item = {'foo': 1}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')

    def test_int_type_value_default(self):
        prototype = PrototypeHandler({'foo': int})
        response = CRUDResponse()
        item = {}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')

    def test_list_type_value_wrong_type(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': list})
        item = {'foo': 1}
        result = prototype.check(item, 'create', response)
        self.assertFalse(result)
        self.assertEqual(response.status, 'error')
        self.assertEqual(response.error_type, 'InvalidType')

    def test_list_type_value_right_type(self):
        prototype = PrototypeHandler({'foo': int})
        response = CRUDResponse()
        item = {'foo': 1}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')

    def test_list_type_value_default(self):
        prototype = PrototypeHandler({'foo': list})
        response = CRUDResponse()
        item = {}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['foo'], [])

    def test_int_value_default(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': 1})
        item = {}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['foo'], 1)

    def test_int_value_right_type(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': 1})
        item = {'foo': 2}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['foo'], 2)

    def test_int_value_wrong_type(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': 1})
        item = {'foo': 2.3}
        result = prototype.check(item, 'create', response)
        self.assertFalse(result)
        self.assertEqual(response.status, 'error')
        self.assertEqual(response.error_type, 'InvalidType')

    def test_int_value_update(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': 1})
        item = {'foo': 2}
        result = prototype.check(item, 'update', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['foo'], 2)

    def test_uuid_value_create(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': '<on-create:uuid>'})
        item = {'bar': 2}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['bar'], 2)
        self.assertTrue(self.uuid_re.match(item['foo']))

    def test_timestamp_value_create(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': '<on-create:timestamp>'})
        item = {'bar': 2}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['bar'], 2)
        self.assertTrue(isinstance(item['foo'], int))

    def test_create_value_only_changes_on_create(self):
        response = CRUDResponse()
        prototype = PrototypeHandler({'foo': '<on-create:timestamp>'})
        item = {'bar': 2}
        result = prototype.check(item, 'create', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['bar'], 2)
        self.assertTrue(isinstance(item['foo'], int))
        ts = item['foo']
        response = CRUDResponse()
        item['bar'] += 1
        result = prototype.check(item, 'update', response)
        self.assertTrue(result)
        self.assertEqual(response.status, 'success')
        self.assertEqual(item['bar'], 3)
        self.assertEqual(item['foo'], ts)
        
