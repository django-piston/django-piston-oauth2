import oauth2 as oauth
from django.contrib.auth.models import User


def generate_random(length=8):
    return User.objects.make_random_password(length=length)


def get_oauth_request(request):
    """ Converts a Django request object into an `oauth2.Request` object. """
    headers = {}
    if 'HTTP_AUTHORIZATION' in request.META:
        headers['Authorization'] = request.META['HTTP_AUTHORIZATION']
    return oauth.Request.from_request(request.method, request.build_absolute_uri(request.path), headers, dict(request.REQUEST))


def verify_oauth_request(request, oauth_request, consumer, token=None):
    """ Helper function to verify requests. """
    from piston.authentication.oauth.store import store

    # Check nonce
    if not store.check_nonce(request, oauth_request, oauth_request['oauth_nonce']):
        return False

    # Verify request
    try:
        oauth_server = oauth.Server()
        oauth_server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())
        oauth_server.add_signature_method(oauth.SignatureMethod_PLAINTEXT())

        consumer = oauth.Consumer(consumer.key.encode('ascii', 'ignore'), consumer.secret.encode('ascii', 'ignore'))
        oauth_server.verify_request(oauth_request, consumer, token)
    except Exception, e:
        return False
    
    return True
