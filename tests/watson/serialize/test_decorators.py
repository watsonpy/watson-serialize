# -*- coding: utf-8 -*-
from watson.http import messages
from tests.watson.serialize import support


class TestDecorators(object):

    def setup(self):
        self.router = support.sample_router()
        self.controller = support.Controller()

    def test_serialize(self):
        self.controller.request = messages.Request.from_environ({})
        output = self.controller.action()
        assert 'name' in output

    def test_pagination_serialize(self):
        self.controller.request = messages.Request.from_environ({})
        output = self.controller.pagination_action()
        assert 'items' in output
        assert output['meta']['total'] == 1

    def test_status_code_serialize(self):
        self.controller.request = messages.Request.from_environ({})
        self.controller.response = messages.Response()
        output = self.controller.error_action()
        assert self.controller.response.status_code == 406
        assert 'message' in output

    def test_args(self):
        self.controller.request = messages.Request.from_environ({
            'QUERY_STRING': 'exclude=enum_value'
        })
        output = self.controller.action()
        assert 'name' in output
        assert 'enum_value' not in output

    def test_nested_args(self):
        self.controller.request = messages.Request.from_environ({
            'QUERY_STRING': 'include=name,id&expand=instance(id, value),instances(id,instance(*))'
        })
        output = self.controller.nested_object_action()
        assert 'name' in output
        assert 'value' in output['instance']
