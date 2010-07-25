import oauth2 as oauth

from piston.authentication.oauth.store import InvalidAccessToken, InvalidConsumer, InvalidRequestToken, Store
from piston.authentication.oauth.utils import generate_random
from piston.models import Nonce, Token, Consumer


class ModelStore(Store):    
    def get_consumer(self, request, oauth_request, consumer_key):
        try:
            consumer = Consumer.objects.get(key=consumer_key)
            return oauth.Consumer(consumer.key, consumer.secret)
        except Consumer.DoesNotExist:
            raise InvalidConsumer

    def get_consumer_from_request_token(self, request, oauth_request, request_token):
        try:
            return Token.objects.get(key=request_token.key, token_type=Token.REQUEST).consumer
        except Token.DoesNotExist:
            raise InvalidConsumer

    def get_consumer_from_access_token(self, request, oauth_request, access_token):
        try:
            return Token.objects.get(key=access_token.key, token_type=Token.ACCESS).consumer
        except Token.DoesNotExist:
            raise InvalidConsumer

    def create_request_token(self, request, oauth_request, consumer, callback):
        token = Token.objects.create_token(
            token_type=Token.REQUEST,
            consumer=Consumer.objects.get(key=oauth_request['oauth_consumer_key']),
            timestamp=oauth_request['oauth_timestamp']
        )
        token.set_callback(callback)
        token.save()    

        return token

    def get_request_token(self, request, oauth_request, request_token_key):
        try:
            return Token.objects.get(key=request_token_key, token_type=Token.REQUEST)
        except Token.DoesNotExist:
            raise InvalidRequestToken

    def authorize_request_token(self, request, oauth_request, request_token):    
        try:
            token = Token.objects.get(key=request_token.key, token_type=Token.REQUEST)
            token.is_approved = True
            token.user = request.user
            token.verifier = oauth.generate_verifier()
            token.save()
            return token
        except Token.DoesNotExist:
            raise InvalidRequestToken

    def create_access_token(self, request, oauth_request, consumer, request_token):
        request_token = Token.objects.get(key=request_token.key, token_type=Token.REQUEST)
        access_token = Token.objects.create_token(
            token_type=Token.ACCESS,
            timestamp=oauth_request['oauth_timestamp'],
            consumer=Consumer.objects.get(key=consumer.key),
            user=request_token.user,
        )
        request_token.delete()
        return access_token

    def get_access_token(self, request, oauth_request, consumer, access_token_key):
        try:
            return Token.objects.get(key=access_token_key, token_type=Token.ACCESS)
        except Token.DoesNotExist:
            raise InvalidAccessToken

    def get_user_from_access_token(self, request, oauth_request, access_token):
        try:
            return Token.objects.get(key=access_token.key, token_type=Token.ACCESS).user
        except Token.DoesNotExist:
            raise InvalidConsumer

    def check_nonce(self, request, oauth_request, nonce):
        nonce, created = Nonce.objects.get_or_create(
            consumer_key=oauth_request['oauth_consumer_key'],
            token_key=oauth_request.get('oauth_token', ''),
            key=nonce
        )
        return created
