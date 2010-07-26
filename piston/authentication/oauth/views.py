import oauth2 as oauth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from piston.authentication.oauth.forms import AuthorizeRequestTokenForm
from piston.authentication.oauth.store import store
from piston.authentication.oauth.utils import verify_oauth_request, get_oauth_request


@csrf_exempt
def get_request_token(request):
    oauth_request = get_oauth_request(request)
    consumer = store.get_consumer(request, oauth_request, oauth_request['oauth_consumer_key'])

    # Ensure the client is using 1.0a
    if 'oauth_callback' not in oauth_request:
        return HttpResponseBadRequest('OAuth 1.0 is not supported, you must use OAuth 1.0a.')

    if not verify_oauth_request(request, oauth_request, consumer):
        return HttpResponseBadRequest()

    request_token = store.create_request_token(request, oauth_request, consumer, oauth_request['oauth_callback'])
    ret = 'oauth_token=%s&oauth_token_secret=%s&callback_confirmed=true' % (request_token.key, request_token.secret)
    return HttpResponse(ret, content_type='application/x-www-form-urlencoded')


@login_required
def authorize_request_token(request, form_class=AuthorizeRequestTokenForm, template_name='piston/oauth/authorize.html', verification_template_name='piston/oauth/authorize_verification_code.html'):
    if 'oauth_token' not in request.REQUEST:
        return HttpResponse('No token specified.')

    oauth_request = get_oauth_request(request)
    request_token = store.get_request_token(request, oauth_request, request.REQUEST['oauth_token'])
    consumer = store.get_consumer_from_request_token(request, oauth_request, request_token)
    
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid() and form.cleaned_data['authorize_access']:
            request_token = store.authorize_request_token(request, oauth_request, request_token)            
            if request_token.callback is not None and request_token.callback != 'oob':
                return HttpResponseRedirect('%s&oauth_token=%s' % (request_token.get_callback_url(), request_token.key))
            else:
                return render_to_response(verification_template_name, {'consumer': consumer, 'verification_code': request_token.verifier}, RequestContext(request))
    else:
        form = form_class(initial={'oauth_token': request_token.key})

    return render_to_response(template_name, {'consumer': consumer, 'form': form}, RequestContext(request))


@csrf_exempt
def get_access_token(request):
    oauth_request = get_oauth_request(request)
    consumer = store.get_consumer(request, oauth_request, oauth_request['oauth_consumer_key'])
    request_token = store.get_request_token(request, oauth_request, oauth_request['oauth_token'])

    if not verify_oauth_request(request, oauth_request, consumer, request_token):
        return HttpResponseBadRequest()
        
    if oauth_request.get('oauth_verifier', None) != request_token.verifier:
        return False

    access_token = store.create_access_token(request, oauth_request, consumer, request_token)
    ret = 'oauth_token=%s&oauth_token_secret=%s' % (access_token.key, access_token.secret)
    return HttpResponse(ret, content_type='application/x-www-form-urlencoded')
