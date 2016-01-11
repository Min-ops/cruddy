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

import re
import uuid
import time

from botocore.vendored.six import string_types


class CalculatedValue(object):

    token_re = re.compile('\<on-(?P<operation>[^\s]+):(?P<token>[^\s]+)\>')
    valid_operations = ['create', 'update']

    @classmethod
    def check(cls, token):
        if isinstance(token, string_types):
            match = cls.token_re.match(token)
            if match:
                operation = match.group('operation')
                if operation in cls.valid_operations:
                    token = match.group('token')
                    token_method_name = '_get_{}'.format(token)
                    token_method = getattr(cls, token_method_name, None)
                    if callable(token_method):
                        return cls(operation, token_method)
        return None

    @classmethod
    def _get_uuid(cls):
        return str(uuid.uuid4())

    @classmethod
    def _get_timestamp(cls):
        return int(time.time() * 1000)

    def __init__(self, operation, token_method):
        self.operation = operation
        self.token_method = token_method

    @property
    def value(self):
        return self.token_method()


