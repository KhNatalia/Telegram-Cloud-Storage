import sys


class TelegramUploadError(Exception):
    body = ''
    error_code = 1

    def __init__(self, extra_body=''):
        self.extra_body = extra_body

    def __str__(self):
        msg = self.__class__.__name__
        if self.body:
            msg += ': {}'.format(self.body)
        if self.extra_body:
            msg += ('. {}' if self.body else ': {}').format(self.extra_body)
        return msg


class TelegramProxyError(TelegramUploadError):
    error_code = 30


class TelegramUploadNoSpaceError(TelegramUploadError):
    error_code = 28


def catch(fn):
    def wrap(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except TelegramUploadError as e:
            sys.stderr.write('[Error] telegram-upload Exception:\n{}\n'.format(e))
            exit(e.error_code)
    return wrap
