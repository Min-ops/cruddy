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

import copy


class CRUDResponse(object):

    def __init__(self, debug=False, response_data=None):
        self._debug = debug
        if response_data:
            self.__dict__.update(response_data)
        else:
            self.status = 'success'
            self.data = None
            self.error_type = None
            self.error_code = None
            self.error_message = None
            self.raw_response = None
            self.metadata = None

    def __repr__(self):
        return 'Status: {}'.format(self.status)

    @property
    def is_successful(self):
        return self.status == 'success'

    def flatten(self):
        flat = copy.deepcopy(self.__dict__)
        hiddens = []
        for k in flat:
            if k.startswith('_'):
                hiddens.append(k)
        for k in hiddens:
            del flat[k]
        return flat

    def prepare(self):
        if self.status == 'success':
            if self.raw_response:
                if not self._debug:
                    md = self.raw_response['ResponseMetadata']
                    self.metadata = md
                    self.raw_response = None
