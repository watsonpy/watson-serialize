# -*- coding: utf-8 -*-
from watson.serialize import serializers, errors

__all__ = ['serialize']


def serialize(func=None, router=None):
    """Serialize an iterable object into a format suitable for encoding.

    A user can add additional query string parameters to the URL in order to
    include/exclude/expand certain fields that are contained in the models
    being exposed.

    Args:
        router (watson.routing.routers.Base): The router to be used, defaults
            to the router retrieved from the container

    Returns:
        A list/dictionary of values suitable for encoding

    Usage:

        .. code-block: python

            class MyModel(models.Base):

                class Meta(object):
                    attributes = ('id', 'name', 'related')
                    route = 'models'

                id = ..
                name = ..
                related = []

            class Controller(controllers.Rest):
                @serialize
                def GET(self):
                    return [
                        MyModel(
                            id=1,
                            name='Test',
                            related=[
                                MyModel(id=5, name='Related model')
                            ])
                    ]

        .. code-block:

            # http://site.url/models?include=id,name
            # Returns MyModel objects with attributes id, and name

            # http://site.url/models?include=*
            # Returns MyModel objects with all attributes in the Meta object

            # http://site.url/models?exclude=name
            # Returns MyModel objects with all attributes in the Meta object excluding
            # the name attribute

            # http://site.url/models?expand=related
            # Returns MyModel objects with all attributes in the Meta object and
            # expand the attributes for the models in the 'related' attribute of MyModel

            # http://site.url/models?expand=related(name)
            # Returns MyModel objects with all attributes in the Meta object and
            # expand the models in the 'related' attribute of MyModel, showing
            # their 'name' attribute
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            serializer_kwargs = {}
            for arg in ('expand', 'include', 'exclude'):
                serializer_kwargs[arg] = serializers.split_attributes(self.request.get[arg]) if arg in self.request.get else None
            try:
                response = func(self, **kwargs)
            except errors.Base as exc:
                response = exc
            use_router = router if router else self.container.get('router')
            serializer = serializers.Instance(use_router)
            if isinstance(response, errors.Base):
                self.response.status_code = response.status_code
            response = serializer(
                response,
                **serializer_kwargs)
            return response
        return wrapper
    return decorator(func) if func else decorator
