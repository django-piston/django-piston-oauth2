import urlparse

import oauth2 as oauth
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import simplejson
from django.conf import settings

from piston.models import Consumer, Token

try:
    import yaml
except ImportError:
    print "Can't run YAML testsuite"
    yaml = None

import urllib, base64

from test_project.apps.testapp.models import TestModel, ExpressiveTestModel, Comment, InheritedModel, Issue58Model, ListFieldsModel
from test_project.apps.testapp import signals


class MainTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('admin', 'admin@world.com', 'admin')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.is_active = True
        self.user.save()
        self.auth_string = 'Basic %s' % base64.encodestring('admin:admin').rstrip()

        if hasattr(self, 'init_delegate'):
            self.init_delegate()
        
    def tearDown(self):
        self.user.delete()



class OAuthTests(MainTests):
    signature_method = oauth.SignatureMethod_HMAC_SHA1()
    callback_url = 'http://example.com/cb'
    request_token_url = 'http://testserver/api/oauth/get_request_token'
    authorize_url = 'http://testserver/api/oauth/authorize_request_token'
    access_token_url = 'http://testserver/api/oauth/get_access_token'
    api_access_url = 'http://testserver/api/oauth/api_access'

    def setUp(self):
        super(OAuthTests, self).setUp()
        self.consumer = Consumer.objects.create_consumer('Test Consumer')
        self.consumer.status = 'accepted'
        self.consumer.save()

    def tearDown(self):
        super(OAuthTests, self).tearDown()
        #self.consumer.delete()

    def test_get_request_token(self, callback='oob'):
        request = oauth.Request.from_consumer_and_token(self.consumer, None, 'GET', self.request_token_url, {'oauth_callback': callback})
        request.sign_request(self.signature_method, self.consumer, None)

        response = self.client.get(self.request_token_url, request)
        self.assertEquals(response.status_code, 200)

        params = dict(urlparse.parse_qsl(response.content))
        return oauth.Token(params['oauth_token'], params['oauth_token_secret'])

    def authorize_request_token(self, request_token_key):
        self.client.login(username='admin', password='admin')
        return self.client.post(self.authorize_url, {'oauth_token': request_token_key, 'authorize_access': None})

    def test_authorize_request_token_without_callback(self):
        request_token = self.test_get_request_token('oob')
        response = self.authorize_request_token(request_token.key)

        self.assertEquals(response.status_code, 200)

    def test_authorize_request_token_with_callback(self):
        request_token = self.test_get_request_token(self.callback_url)
        response = self.authorize_request_token(request_token.key)

        self.assertEquals(response.status_code, 302)
        self.assert_(response['Location'].startswith(self.callback_url))
        return response

    def test_get_access_token(self):
        request_token = self.test_get_request_token(self.callback_url)
        response = self.authorize_request_token(request_token.key)
        params = dict(urlparse.parse_qsl(response['Location'][len(self.callback_url)+1:]))
        
        request_token.set_verifier(params['oauth_verifier'])
        
        request = oauth.Request.from_consumer_and_token(self.consumer, request_token, 'POST', self.access_token_url)
        request.sign_request(self.signature_method, self.consumer, request_token)

        response = self.client.post(self.access_token_url, request)
        self.assertEquals(response.status_code, 200)
        
        params = dict(urlparse.parse_qsl(response.content))
        return oauth.Token(params['oauth_token'], params['oauth_token_secret'])

    def test_api_access(self):
        access_token = self.test_get_access_token()

        request = oauth.Request.from_consumer_and_token(self.consumer, access_token, 'GET', self.api_access_url, {'msg': 'expected response'})
        request.sign_request(self.signature_method, self.consumer, access_token)

        response = self.client.get(self.api_access_url, request)
        self.assertEquals(response.status_code, 200)
        self.assert_('expected response' in response.content)


class BasicAuthTest(MainTests):

    def test_invalid_auth_header(self):
        response = self.client.get('/api/entries/')
        self.assertEquals(response.status_code, 401)

        # no space
        bad_auth_string = 'Basic%s' % base64.encodestring('admin:admin').rstrip()
        response = self.client.get('/api/entries/',
            HTTP_AUTHORIZATION=bad_auth_string)
        self.assertEquals(response.status_code, 401)

        # no colon
        bad_auth_string = 'Basic %s' % base64.encodestring('adminadmin').rstrip()
        response = self.client.get('/api/entries/',
            HTTP_AUTHORIZATION=bad_auth_string)
        self.assertEquals(response.status_code, 401)

        # non base64 data
        bad_auth_string = 'Basic FOOBARQ!'
        response = self.client.get('/api/entries/',
            HTTP_AUTHORIZATION=bad_auth_string)
        self.assertEquals(response.status_code, 401)

class TestMultipleAuthenticators(MainTests):
    def test_both_authenticators(self):
        for username, password in (('admin', 'admin'), 
                                   ('admin', 'secr3t'),
                                   ('admin', 'user'),
                                   ('admin', 'allwork'),
                                   ('admin', 'thisisneat')):
            auth_string = 'Basic %s' % base64.encodestring('%s:%s' % (username, password)).rstrip()

            response = self.client.get('/api/multiauth/',
                HTTP_AUTHORIZATION=auth_string)

            self.assertEquals(response.status_code, 200, 'Failed with combo of %s:%s' % (username, password))

class MultiXMLTests(MainTests):
    def init_delegate(self):
        self.t1_data = TestModel()
        self.t1_data.save()
        self.t2_data = TestModel()
        self.t2_data.save()

    def test_multixml(self):
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<response><resource><test1>None</test1><test2>None</test2></resource><resource><test1>None</test1><test2>None</test2></resource></response>'
        result = self.client.get('/api/entries.xml',
                HTTP_AUTHORIZATION=self.auth_string).content
        self.assertEquals(expected, result)

    def test_singlexml(self):
        obj = TestModel.objects.all()[0]
        expected = '<?xml version="1.0" encoding="utf-8"?>\n<response><test1>None</test1><test2>None</test2></response>'
        result = self.client.get('/api/entry-%d.xml' % (obj.pk,),
                HTTP_AUTHORIZATION=self.auth_string).content
        self.assertEquals(expected, result)

class AbstractBaseClassTests(MainTests):
    def init_delegate(self):
        self.ab1 = InheritedModel()
        self.ab1.save()
        self.ab2 = InheritedModel()
        self.ab2.save()
        
    def test_field_presence(self):
        result = self.client.get('/api/abstract.json',
                HTTP_AUTHORIZATION=self.auth_string).content
                
        expected = """[
    {
        "id": 1, 
        "some_other": "something else", 
        "some_field": "something here"
    }, 
    {
        "id": 2, 
        "some_other": "something else", 
        "some_field": "something here"
    }
]"""
        
        self.assertEquals(result, expected)

    def test_specific_id(self):
        ids = (1, 2)
        be = """{
    "id": %d, 
    "some_other": "something else", 
    "some_field": "something here"
}"""
        
        for id_ in ids:
            result = self.client.get('/api/abstract/%d.json' % id_,
                    HTTP_AUTHORIZATION=self.auth_string).content
                    
            expected = be % id_
            
            self.assertEquals(result, expected)

class IncomingExpressiveTests(MainTests):
    def init_delegate(self):
        e1 = ExpressiveTestModel(title="foo", content="bar")
        e1.save()
        e2 = ExpressiveTestModel(title="foo2", content="bar2")
        e2.save()

    def test_incoming_json(self):
        outgoing = simplejson.dumps({ 'title': 'test', 'content': 'test',
                                      'comments': [ { 'content': 'test1' },
                                                    { 'content': 'test2' } ] })
    
        expected = """[
    {
        "content": "bar", 
        "comments": [], 
        "title": "foo"
    }, 
    {
        "content": "bar2", 
        "comments": [], 
        "title": "foo2"
    }
]"""
    
        result = self.client.get('/api/expressive.json',
            HTTP_AUTHORIZATION=self.auth_string).content

        self.assertEquals(result, expected)
        
        resp = self.client.post('/api/expressive.json', outgoing, content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_string)
            
        self.assertEquals(resp.status_code, 201)
        
        expected = """[
    {
        "content": "bar", 
        "comments": [], 
        "title": "foo"
    }, 
    {
        "content": "bar2", 
        "comments": [], 
        "title": "foo2"
    }, 
    {
        "content": "test", 
        "comments": [
            {
                "content": "test1"
            }, 
            {
                "content": "test2"
            }
        ], 
        "title": "test"
    }
]"""
        
        result = self.client.get('/api/expressive.json', 
            HTTP_AUTHORIZATION=self.auth_string).content
            
        self.assertEquals(result, expected)

    def test_incoming_invalid_json(self):
        resp = self.client.post('/api/expressive.json',
            'foo',
            HTTP_AUTHORIZATION=self.auth_string,
            content_type='application/json')
        self.assertEquals(resp.status_code, 400)

    def test_incoming_yaml(self):
        if not yaml:
            return
            
        expected = """- comments: []
  content: bar
  title: foo
- comments: []
  content: bar2
  title: foo2
"""
          
        self.assertEquals(self.client.get('/api/expressive.yaml',
            HTTP_AUTHORIZATION=self.auth_string).content, expected)

        outgoing = yaml.dump({ 'title': 'test', 'content': 'test',
                                      'comments': [ { 'content': 'test1' },
                                                    { 'content': 'test2' } ] })
            
        resp = self.client.post('/api/expressive.json', outgoing, content_type='application/x-yaml',
            HTTP_AUTHORIZATION=self.auth_string)
        
        self.assertEquals(resp.status_code, 201)
        
        expected = """- comments: []
  content: bar
  title: foo
- comments: []
  content: bar2
  title: foo2
- comments:
  - {content: test1}
  - {content: test2}
  content: test
  title: test
"""
        self.assertEquals(self.client.get('/api/expressive.yaml', 
            HTTP_AUTHORIZATION=self.auth_string).content, expected)

    def test_incoming_invalid_yaml(self):
        resp = self.client.post('/api/expressive.yaml',
            '  8**sad asj lja foo',
            HTTP_AUTHORIZATION=self.auth_string,
            content_type='application/x-yaml')
        self.assertEquals(resp.status_code, 400)

class Issue36RegressionTests(MainTests):
    """
    This testcase addresses #36 in django-piston where request.FILES is passed
    empty to the handler if the request.method is PUT.
    """
    def fetch_request(self, sender, request, *args, **kwargs):
        self.request = request

    def setUp(self):
        super(self.__class__, self).setUp()
        self.data = TestModel()
        self.data.save()
        # Register to the WSGIRequest signals to get the latest generated
        # request object.
        signals.entry_request_started.connect(self.fetch_request)

    def tearDown(self):
        super(self.__class__, self).tearDown()
        self.data.delete()
        signals.entry_request_started.disconnect(self.fetch_request)
    
    def test_simple(self):
        # First try it with POST to see if it works there
        if True:
            fp = open(__file__, 'r')
            try:
                response = self.client.post('/api/entries.xml',
                        {'file':fp}, HTTP_AUTHORIZATION=self.auth_string)
                self.assertEquals(1, len(self.request.FILES), 'request.FILES on POST is empty when it should contain 1 file')
            finally:
                fp.close()

        if not hasattr(self.client, 'put'):
            import warnings
            warnings.warn('Issue36RegressionTest partially requires Django 1.1 or newer. Skipped.')
            return

        # ... and then with PUT
        fp = open(__file__, 'r')
        try:
            response = self.client.put('/api/entry-%d.xml' % self.data.pk,
                    {'file': fp}, HTTP_AUTHORIZATION=self.auth_string)
            self.assertEquals(1, len(self.request.FILES), 'request.FILES on PUT is empty when it should contain 1 file')
        finally:
            fp.close()

class ValidationTest(MainTests):
    def test_basic_validation_fails(self):
        resp = self.client.get('/api/echo')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.content, 'Bad Request <ul class="errorlist">'
            '<li>msg<ul class="errorlist"><li>This field is required.</li>'
            '</ul></li></ul>')

    def test_basic_validation_succeeds(self):
        data = {'msg': 'donuts!'}
        resp = self.client.get('/api/echo', data)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(data, simplejson.loads(resp.content))

class PlainOldObject(MainTests):
    def test_plain_object_serialization(self):
        resp = self.client.get('/api/popo')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals({'type': 'plain', 'field': 'a field'}, simplejson.loads(resp.content))

class ListFieldsTest(MainTests):
    def init_delegate(self):
        ListFieldsModel(kind='fruit', variety='apple', color='green').save()
        ListFieldsModel(kind='vegetable', variety='carrot', color='orange').save()
        ListFieldsModel(kind='animal', variety='dog', color='brown').save()

    def test_single_item(self):
        expect = '''{
    "color": "green", 
    "kind": "fruit", 
    "id": 1, 
    "variety": "apple"
}'''
        resp = self.client.get('/api/list_fields/1')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.content, expect)


    def test_multiple_items(self):
        expect = '''[
    {
        "id": 1, 
        "variety": "apple"
    }, 
    {
        "id": 2, 
        "variety": "carrot"
    }, 
    {
        "id": 3, 
        "variety": "dog"
    }
]'''
        resp = self.client.get('/api/list_fields')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.content, expect)
        
class Issue58ModelTests(MainTests):
    """
    This testcase addresses #58 in django-piston where if a model
    has one of the ['read','update','delete','create'] defined
    it make piston crash with a `TypeError`
    """
    def init_delegate(self):
        m1 = Issue58Model(read=True,model='t') 
        m1.save()
        m2 = Issue58Model(read=False,model='f')
        m2.save()

    def test_incoming_json(self):
        outgoing = simplejson.dumps({ 'read': True, 'model': 'T'})

        expected = """[
    {
        "read": true, 
        "model": "t"
    }, 
    {
        "read": false, 
        "model": "f"
    }
]"""

        # test GET
        result = self.client.get('/api/issue58.json',
                                HTTP_AUTHORIZATION=self.auth_string).content
        self.assertEquals(result, expected)

        # test POST
        resp = self.client.post('/api/issue58.json', outgoing, content_type='application/json',
                                HTTP_AUTHORIZATION=self.auth_string)
        self.assertEquals(resp.status_code, 201)
        