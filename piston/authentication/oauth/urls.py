from django.conf.urls.defaults import *


urlpatterns = patterns('piston.authentication.oauth.views',
    (r'^get_request_token', 'get_request_token'),
    (r'^authorize_request_token', 'authorize_request_token'),
    (r'^get_access_token', 'get_access_token'),
)
