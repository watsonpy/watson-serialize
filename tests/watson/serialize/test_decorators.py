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
