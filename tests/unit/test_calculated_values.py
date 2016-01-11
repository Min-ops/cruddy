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
import time

from cruddy.calculatedvalue import CalculatedValue


class TestCalculatedValue(unittest.TestCase):

    def setUp(self):
        self.uuid_re = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

    def tearDown(self):
        pass

    def test_uuid_create(self):
        cv = CalculatedValue.check('<on-create:uuid>')
        self.assertEqual(cv.operation, 'create')
        self.assertTrue(self.uuid_re.match(cv.value))

    def test_uuid_update(self):
        cv = CalculatedValue.check('<on-update:uuid>')
        self.assertEqual(cv.operation, 'update')
        self.assertTrue(self.uuid_re.match(cv.value))

    def test_ts_create(self):
        cv = CalculatedValue.check('<on-create:timestamp>')
        before = int(time.time() * 1000)
        self.assertEqual(cv.operation, 'create')
        self.assertGreaterEqual(cv.value, before)
        self.assertLessEqual(cv.value, int(time.time() * 1000))

    def test_bad_operation(self):
        cv = CalculatedValue.check('<on-foobar:uuid>')
        self.assertIsNone(cv)

    def test_bad_token(self):
        cv = CalculatedValue.check('<on-create:foobar>')
        self.assertIsNone(cv)
