from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib


class InvalidConsumer(RuntimeError):
    pass


class InvalidToken(RuntimeError):
    pass


class InvalidRequestToken(InvalidToken):
    pass


class InvalidAccessToken(InvalidToken):
    pass


class Store(object):
    def get_consumer(self, request, oauth_request, consumer_key):
        """
        Return an `oauth2.Consumer` (or compatible) instance for `consumer_key`
        or raise `InvalidConsumer`.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `consumer_key`: The consumer key.
        """
        raise NotImplementedError
    
    def get_consumer_from_request_token(self, request, oauth_request, request_token):
        """
        Return the `oauth2.Consumer` (or compatible) instance associated with
        the `request_token` request token, or raise `InvalidConsumer`.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `request_token`: The request token to get the consumer for.
        """
        raise NotImplementedError
    
    def get_consumer_from_access_token(self, request, oauth_request, access_token):
        """
        Return the `oauth2.Consumer` (or compatible) instance associated with
        the `access_token` access token, or raise `InvalidConsumer`.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `access_token`: The access token to get the consumer for.
        """
        raise NotImplementedError
        
    def create_request_token(self, request, oauth_request, consumer, callback):
        """
        Generate and return an `oauth2.Token` (or compatible) instance.

        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `consumer`: The consumer that made the request.
        """
        raise NotImplementedError

    def get_request_token(self, request, oauth_request, request_token_key):
        """
        Return an `oauth2.Token` (or compatible) instance for
        `request_token_key` or raise `InvalidRequestToken`.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `consumer`: The consumer that made the request.
        `request_token_key`: The request token key.
        """
        raise NotImplementedError

    def authorize_request_token(self, request, oauth_request, request_token):
        """ 
        Authorize the request token and return it, or raise
        `InvalidRequestToken`.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `request_token`: The request token.
        """
        raise NotImplementedError

    def create_access_token(self, request, oauth_request, consumer, request_token):
        """
        Generate and return a `oauth2.Token` (or compatible) instance.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `consumer`: The consumer that made the request.
        `request_token`: The request token used to request the access token.
        """
        raise NotImplementedError

    def get_access_token(self, request, oauth_request, consumer, access_token_key):
        """
        Return the appropriate `oauth2.Token` (or compatible) instance for
        `access_token_key` or raise `InvalidAccessToken`.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `consumer`: The consumer that made the request.
        `access_token_key`: The access token key used to make the request.
        """
        raise NotImplementedError

    def check_nonce(self, request, oauth_request, nonce):
        """
        Return `True` if the nonce has not yet been used.
        
        `request`: The Django request object.
        `oauth_request`: The `oauth2.Request` object.
        `nonce`: The nonce to check.
        """
        raise NotImplementedError


def get_store(path='piston.authentication.oauth.store.db.ModelStore'):
    """
    Load the piston oauth store. Should not be called directly unless testing.
    """
    path = getattr(settings, 'PISTON_OAUTH_STORE', path)

    try:
        module, attr = path.rsplit('.', 1)
        store_class = getattr(importlib.import_module(module), attr)
    except ValueError:
        raise ImproperlyConfigured('Invalid piston oauth store string: "%s"' % path)
    except ImportError, e:
        raise ImproperlyConfigured('Error loading piston oauth store module "%s": "%s"' % (module, e))
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a piston oauth store named "%s"' % (module, attr))

    return store_class()


store = get_store()
