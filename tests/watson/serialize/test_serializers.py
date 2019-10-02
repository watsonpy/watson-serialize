# -*- coding: utf-8 -*-
from tests.watson.serialize import support
from watson.db import utils
from watson.serialize import serializers


class TestInstance(object):

    def setup(self):
        self.router = support.sample_router()
        self.serializer = serializers.Instance(self.router)

    def test_serialize_none(self):
        output = self.serializer(None)
        assert not output

    def test_serialize_list(self):
        model = support.generate_model(id=1, name='test')
        objs = [model]
        output = self.serializer(objs)
        assert output['items'][0]['name'] == 'test'

    def test_serialize_list_identifier_only(self):
        model = support.generate_model(id=1, name='test')
        model.Meta.expand = False
        objs = [model]
        output = self.serializer(objs)
        assert 'name' not in output['items'][0]
        output = self.serializer(objs, expand=['name'])
        assert 'name' in output['items'][0]

    def test_serialize(self):
        model = support.generate_model(id=1, name='test')
        output = self.serializer(model)
        assert output['name'] == 'test'

    def test_include_all(self):
        model = support.generate_model(id=1, name='test', instances=4)
        output = self.serializer(model)
        assert output['name'] == 'test'
        assert output['id'] == 1
        assert output['instances'] == 4

    def test_include_all_wildcard(self):
        model = support.generate_model(id=1, name='test')
        output = self.serializer(model, include=['*'])
        assert output['name'] == 'test'
        assert output['id'] == 1
        assert 'instances' in output
        assert not output['instances']

    def test_include_identifier_only(self):
        model = support.generate_model(id=1, name='test')
        output = self.serializer(model, include=['id'])
        assert 'name' not in output
        assert 'id' in output

    def test_exclude(self):
        model = support.generate_model(id=1, name='test', instances=4)
        output = self.serializer(model, exclude=['instances'])
        assert output['name'] == 'test'
        assert output['id'] == 1
        assert 'instances' not in output

    def test_expand_object(self):
        model = support.generate_model(
            id=1,
            name='test',
            instances=support.SubModel(id=1, value='testing'))
        output = self.serializer(model)
        assert output['instances']
        assert 'value' not in output['instances']

    def test_expand_wildcard(self):
        model = support.generate_model(
            id=1,
            name='test',
            instances=support.SubModel(id=1, value='testing'))
        output = self.serializer(model, expand=['instances(*)'])
        assert output['instances']
        assert 'value' in output['instances']
        assert output['instances']['value']

    def test_expand_child_include(self):
        model = support.generate_model(
            id=1,
            name='test',
            instances=support.SubModel(id=1, value='testing'))
        output = self.serializer(model, expand=['instances(id)'])
        assert output['instances']
        assert 'value' not in output['instances']

    def test_expand_list(self):
        model = support.generate_model(
            id=1,
            name='test',
            instances=[
                support.SubModel(id=1, value='testing')
            ])
        output = self.serializer(model, expand=['instances(*)'])
        assert output['instances']
        assert output['instances']['items'][0]['value'] == 'testing'

    def test_strategies(self):
        model = support.generate_model(id=1)
        output = self.serializer(model)
        assert output['enum_value'] == 'test'

    def test_null_values(self):
        model = support.generate_model(id=1)
        self.serializer.include_null = True
        output = self.serializer(model)
        assert 'name' in output

    def test_protected_values(self):
        model = support.generate_model(id=1, name='Test')
        output = self.serializer(
            model, include=['protected_value', 'name', 'id'])
        assert 'protected_value' not in output

    def test_repr(self):
        model = support.generate_model(id=1, name='Test')
        self.serializer(model)
        assert repr(self.serializer)

    def test_paginator_object(self):
        repository = support.sample_repository()
        paginator = utils.Pagination(repository.query)
        output = self.serializer(paginator)
        assert 'items' in output
        assert output['meta']['total'] == 1

    def test_meta_attachment(self):
        repository = support.sample_repository()
        paginator = utils.Pagination(repository.query)
        output = self.serializer(paginator)
        assert output['meta']['href'] == '/models?page=1'

    def test_camelcased_names(self):
        model = support.generate_model(id=1)
        output = self.serializer(model, include=['enumValue'])
        assert 'enum_value' in output


class TestAttributes(object):
    def test_split_attributes(self):
        string = 'attr'
        assert serializers.split_attributes(string)[0] == 'attr'
        string = 'attr(attr),attr2,attr3(attr4,attr5(attr6(attr7)),attr9),attr10'
        split_string = serializers.split_attributes(string)
        assert split_string[0] == 'attr(attr)'
        assert split_string[1] == 'attr2'
        assert split_string[2] == 'attr3(attr4,attr5(attr6(attr7)),attr9)'
        string = 'attr(attr(attr3(attr4))),attr2,attr6'
        split_string = serializers.split_attributes(string)
        assert split_string[0] == 'attr(attr(attr3(attr4)))'
        assert split_string[1] == 'attr2'
        assert split_string[2] == 'attr6'
