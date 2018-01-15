# -*- coding: utf-8 -*-
class Base(RuntimeError):
    """An extendible class for responding to exceptions caused within your application.

    Usage:

        .. code-block: python

            class MyRestError(errors.Base):
                pass

            # somewhere in your code...

            raise MyRestError(code=01, message='You broke it', developer_message='Invalid index supplied')

            # {'code': '01406', message='You broke it', 'developer_message': 'Invalid index supplied'}
    """

    class Meta(object):
        attributes = (
            'code',
            'status',
            'message',
            'developer_message')

    def __init__(
            self,
            code,
            message='Unknown Error',
            status_code=406,
            developer_message=None):
        """Initialize the error.

        Args:
            code (int/string): A unique exception code for the error, gets combined with the status_code
            status_code (int): The HTTP status code associated with the response (see https://httpstatuses.com/)
            message (string): A human friendly exception message
            developer_message (string): A more complex exception message aimed at deveopers
        """
        super(Base, self).__init__(message)
        self.status_code = status_code
        self.code = '{}{}'.format(status_code, code)
        self.message = message
        self.developer_message = '{}: {}'.format(
            self.__class__.__name__,
            developer_message or message)
