# -*- coding: utf-8 -*-
import abc
import collections
import re
from watson.common import imports, strings
from watson.db import utils

# splits attribute(attr1,attr2),attribute2 by comma
attribute_regex = r',(?![^()]*(?:\([^()]*\))?\))'


class Base(metaclass=abc.ABCMeta):

    router = None

    def __init__(self, router):
        self.router = router

    @classmethod
    def from_meta(cls, meta, router):
        serializer = getattr(meta, 'class_', cls)(router)
        serializer.meta = meta
        return serializer


class Instance(Base):

    """Serialize an iterable object into a format suitable for json encoding.

    Attributes:
        include_name (boolean): Whether or not to include null values in the output
        strategies
        type (mixed): The class name of the object being serialized

    Returns:
        A list of objects that are suitable to be json encoded

    Usage:

        .. code-block: python

            class SomeClass(object):

                class Meta(serializers.Instance):
                    attributes = ('id',)

                id = None

            serializer = serializers.Collection(router)
            serializer([SomeClass()])  # [{'id': 'value of id attribute'}]
    """

    type = None
    meta = None
    expand = True
    include_null = None

    @property
    def identifier(self):
        """Unique identifier for the object being serialized.

        Defaults to the first

        Returns:
            string: The first value from the attributes Meta class.
        """
        return self.meta.attributes[0]

    @property
    def attributes(self):
        return self.meta.attributes

    @property
    def strategies(self):
        return getattr(self.meta, 'strategies', None)

    @property
    def expose_meta(self):
        return getattr(self.meta, 'expose_meta', True)

    def _assign_meta(self, instance):
        if not self.meta and hasattr(instance, 'Meta'):
            self.type = instance.__class__
            self.meta = instance.Meta
            self.expand = getattr(instance.Meta, 'expand', True)
            if self.include_null is None:
                self.include_null = getattr(instance.Meta, 'include_null', False)

    def _cleaned_attribute_names(self, accepted, requested, override):
        override = set([
            strings.snakecase(attr) for attr in set(
                override).difference(accepted)
        ])
        return accepted.union(requested.intersection(override))

    def _generate_attributes(self, expand=None, include=None, exclude=None):
        if include and include[0] == '*':
            self.include_null = True
            include.remove('*')
        _attributes = set(self.attributes)
        if not include:
            attributes = _attributes
        else:
            attributes = set([self.identifier])
        if include:
            attributes = self._cleaned_attribute_names(
                attributes, _attributes, include)
        if exclude:
            try:
                exclude.remove(self.identifier)
            except ValueError:
                pass
            attributes = attributes - set(exclude)
        if expand:
            attributes = self._cleaned_attribute_names(
                attributes, _attributes, expand)
        return attributes

    def _generate_expands(self, expands=None):
        output = {}
        for expand in expands or []:
            m = re.search('(\w+)\((.*)\)', expand)
            if not m:
                output[expand] = None
                continue
            output[strings.snakecase(m.group(1))] = [
                v.strip() for v in re.split(attribute_regex, m.group(2))
            ]
        return output

    def _serialize_collection(
            self, values, expand=None, include=None, exclude=None):
        output = []
        for value in values:
            self._assign_meta(value)
            if not self.expand:
                include = [self.identifier]
            value = self._serialize_instance(
                value, expand=expand, include=include, exclude=exclude)
            output.append(value)
        return output

    def _includes_expands_from_expand(self, expand):
        expands = []
        includes = []
        for expand_ in expand or []:
            if '(' in expand_:
                expands.append(expand_)
            else:
                includes.append(expand_)
        return includes, expands

    def _serialize_instance(
            self, instance, expand=None, include=None, exclude=None):
        if not instance:
            return None
        self._assign_meta(instance)
        obj = {}
        expands = self._generate_expands(expand)
        for attr in self._generate_attributes(expands.keys(), include, exclude):
            if not hasattr(instance, attr):
                continue
            value = getattr(instance, attr)
            if value or self.include_null:
                if isinstance(value, list):
                    serializer = Instance(self.router)
                    sub_includes, sub_expands = self._includes_expands_from_expand(
                        expands.get(attr))
                    if sub_includes:
                        serializer.expand = True
                    value = serializer(
                        value,
                        include=sub_includes, expand=sub_expands)
                elif self.strategies and attr in self.strategies:
                    value = self.strategies[attr](value)
                elif hasattr(value, 'Meta'):
                    serializer = Instance.from_meta(
                        value.Meta, router=self.router)
                    sub_includes, sub_expands = self._includes_expands_from_expand(
                        expands.get(attr))
                    if not sub_includes:
                        sub_includes = [serializer.identifier]
                    value = serializer(
                        value, include=sub_includes, expand=sub_expands)
                obj[attr] = value
        return self._attach_object_meta(obj)

    def _attach_object_meta(self, instance):
        if not hasattr(self.meta, 'route') or not self.expose_meta:
            return instance
        instance['meta'] = {
            'href': self.router.assemble(
                self.meta.route, **{self.identifier: instance[self.identifier]})
        }
        return instance

    def _attach_collection_meta(self, obj, instance):
        if not self.expose_meta:
            return obj
        obj = {
            'items': obj
        }
        is_paginator = isinstance(instance, utils.Pagination)
        pages = ''
        page = 1
        limit = 0
        total = 0
        if is_paginator:
            limit = instance.limit
            total = instance.total
            page = instance.page
            pages = [str(page) for page in instance.iter_pages() if page.id == instance.page]
        else:
            total = len(obj['items'])
            limit = total
        obj['meta'] = {
            'limit': limit,
            'page': page,
            'total': total
        }
        if hasattr(self.meta, 'route'):
            obj['meta']['href'] = '{}{}'.format(
                self.router.assemble(self.meta.route), ''.join(pages))
        return obj

    def _serialize(self, instance, expand=None, include=None, exclude=None):
        is_iterable = isinstance(instance, collections.Iterable)
        serialize_method = '_serialize_instance'
        if is_iterable:
            serialize_method = '_serialize_collection'
        obj = getattr(self, serialize_method)(
            instance, expand, include, exclude)
        if is_iterable:
            obj = self._attach_collection_meta(obj, instance)
        return obj

    def __call__(self, instance, expand=None, include=None, exclude=None):
        """Serialize an object.

        Args:
            instance (mixed): The object to be serialized
            expand (list): Attributes to be expanded on the object
            include (list): Attributes to be included in the output
            exclude (list): Attributes to be excluded from the list

        Return:
            A list/dictionary representation of the instance
        """
        return self._serialize(
            instance, expand=expand, include=include, exclude=exclude)

    def __repr__(self):
        return '<{0} type:{1} include null:{2} expand:{3} attributes:{4}>'.format(
            imports.get_qualified_name(self),
            imports.get_qualified_name(self.type),
            self.include_null,
            self.expand,
            ','.join(self.attributes))
