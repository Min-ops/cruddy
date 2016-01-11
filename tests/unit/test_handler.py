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
import os

import mock
import placebo

import cruddy


class TestCRUDHandler(unittest.TestCase):

    def setUp(self):
        self.environ = {}
        self.environ_patch = mock.patch('os.environ', self.environ)
        self.environ_patch.start()
        credential_path = os.path.join(os.path.dirname(__file__), 'cfg',
                                       'aws_credentials')
        self.environ['AWS_SHARED_CREDENTIALS_FILE'] = credential_path
        self.data_path = os.path.join(os.path.dirname(__file__), 'responses')
        self.crud = cruddy.CRUD(
            profile_name='foobar',
            region_name='us-west-2',
            table_name='mg-test-cruddy',
            prototype={'id': '<on-create:uuid>',
                       'created_at': '<on-create:timestamp>',
                       'modified_at': '<on-update:timestamp>',
                       'fie': 1},
            placebo=placebo,
            placebo_mode='playback',
            placebo_dir=self.data_path)

    def tearDown(self):
        pass

    def test_cruddy(self):
        params = {'operation': 'list'}
        r = self.crud.handler(**params)
        self.assertEqual(r.status, 'success')
        self.assertEqual(len(r.data), 0)
        params = {'operation': 'create',
                  'item': {}}
        r = self.crud.handler(**params)
        item = r.data
        self.assertEqual(r.status, 'success')
        self.assertEqual(item['fie'], 1)
        self.assertTrue(isinstance(item['created_at'], int))
        self.assertTrue(isinstance(item['modified_at'], int))
        params = {'operation': 'list'}
        r = self.crud.handler(**params)
        self.assertEqual(r.status, 'success')
        self.assertEqual(len(r.data), 1)
        item['fie'] = 2
        params = {'operation': 'update',
                  'item': item}
        r = self.crud.handler(**params)
        self.assertEqual(r.status, 'success')
        params = {'operation': 'delete',
                  'id': item['id']}
        r = self.crud.handler(**params)
        self.assertEqual(r.status, 'success')
        params = {'operation': 'list'}
        r = self.crud.handler(**params)
        self.assertEqual(r.status, 'success')
        self.assertEqual(len(r.data), 0)
