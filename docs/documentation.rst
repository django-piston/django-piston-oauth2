.. _documentation:

=============================
Django Piston's documentation
=============================

.. toctree::
   :maxdepth: 4	

---------------
Getting Started
---------------

Getting started with Piston is easy. Your API code will look and behave just like any other Django application. It will have an URL mapping and handlers defining resources.

To get started, it is recommended that you place your API code in a separate folder, e.g. 'api'.

Your application layout could look like this::

    urls.py
    settings.py
    myapp/
       __init__.py
       views.py
       models.py
    api/
       __init__.py
       urls.py
       handlers.py

Then, define a "namespace" where your API will live in your top-level urls.py, like so::

    #!python
    
    urlpatterns = patterns('',
       # all my other url mappings
       (r'^api/', include('mysite.api.urls')),
    )

This will include the API's urls.py for anything beginning with 'api/'.

Next up we'll look at how we can create resources and how to map URLs to them.

---------
Resources
---------

A "Resource" is an entity mapping some kind of resource in code. This could be a blog post, a forum or even something completely arbitrary.

Let's start out by creating a simple handler in handlers.py::

    #!python

    from piston.handler import BaseHandler
    from myapp.models import Blogpost
    
    class BlogpostHandler(BaseHandler):
       allowed_methods = ('GET',)
       model = Blogpost   
    
       def read(self, request, post_slug):
          ...

Piston lets you map resource to models, and by doing so, it will do a lot of the heavy lifting for you.

A resource can be just a class, but usually you would want to define at least 1 of 4 methods:
  
 :read: is called on **GET** requests, and should never modify data (idempotent.)

 :create: is called on **POST**, and creates new objects, and should return them (or :ref:`rc.CREATED`.)

 :update: is called on **PUT**, and should update an existing product and return them (or :ref:`rc.ALL_OK`.)

 :delete: is called on **DELETE**, and should delete an existing object. Should not return anything, just :ref:`rc.DELETED`.

In addition to these, you may define any other methods you want. You can use these by including their names in the  ``fields`` directive, and by doing so, the function will be called with a single argument: The instance of the ``model``. It can then return anything, and the return value will be used as the value for that key.

**NB**: These "resource methods" should be decorated with the @classmethod decorator, as they will not always receive an instance of itself. For example, if you have a UserHandler defined, and you return a User from another handler, you will not receive an instance of that handler, but rather the UserHandler.

Since a single handler can be responsible for both single- and multiple-object data sets, you can differentiate between them in the read() method like so::

    #!python
    
    from piston.handler import BaseHandler
    from myapp.models import Blogpost
    
    class BlogpostHandler(BaseHandler):
        allowed_methods = ('GET',)
        model = Blogpost   
    
        def read(self, request, blogpost_id=None):
            """
            Returns a single post if `blogpost_id` is given,
            otherwise a subset.
    
            """
            base = Blogpost.objects
            
            if blogpost_id:
                return base.get(pk=blogpost_id)
            else:
                return base.all() # Or base.filter(...)


--------
Emitters
--------

Emitters are what spews out the data, and are the things responsible for speaking YAML, JSON, XML, Pickle and Django. They currently reside in ``emitters.py`` as ``XMLEmitter``, ``JSONEmitter``, ``YAMLEmitter``, ``PickleEmitter`` and ``DjangoEmitter``.

Writing your own emitters is easy, all you have to do is create a class that subclasses ``Emitter`` and has a ``render`` method. The render method will receive 1 argument, 'request', which is a copy of the request object, which is useful if you need to look at request.GET (like defining callbacks, like the JSON emitter does.)

To get the data to serialize/render, you can call ``self.construct()`` which always returns a dictionary. From there, you can do whatever you want with the data and return it (as a unicode string.)

**NB**: New in <<cset 23ebc37c78e8>>: Emitters can now be registered with the ``Emitter.register`` function, and can be removed (in case you want to remove a built-in emitter) via the ``Emitter.unregister`` function.

The built-in emitters are registered like so::

    #!python
    
    class JSONEmitter(Emitter):
        ...
    
    Emitter.register('json', JSONEmitter, 'application/json; charset=utf-8')

If you write your own emitters, you can import Emitter and call 'register' on it to put your emitter into action. You can also overwrite built-in, or existing emitters, by using the same name (the first argument.)

This makes it very easy to add support for extended formats, like protocol buffers or CSV.

Emitters are accessed via the ?format GET argument, e.g. '/api/blogposts/?format=yaml', but since <<cset 23ebc37c78e8>>, it is now possible to access them via a special keyword argument in your URL mapping. This keyword is called 'emitter_format' (to not clash with your own 'format' keyword), and can be used like so::

    #!python
    
    urlpatterns = patterns('',
       url(r'^blogposts(?P<emitter_format>.+)$', ...),
    )

Now a request for /blogposts.json will use the JSON emitter, etc.

Additionally, you may specify the format in your URL mapping, via the keyword arguments shortcut::

    #!python
    
    urlpatterns = patterns('',
       url(r'^blogposts$', resource_here, { 'emitter_format': 'json' }),
    )

------------
Mapping URLs
------------

URL mappings in Piston work just like they do in Django. Lets map our BlogpostHandler:

In urls.py::

    #!python
    
    from django.conf.urls.defaults import *
    from piston.resource import Resource
    from mysite.myapp.api.handlers import BlogpostHandler
    
    blogpost_handler = Resource(BlogpostHandler)
    
    urlpatterns = patterns('',
       url(r'^blogpost/(?P<post_slug>[^/]+)/', blogpost_handler),
       url(r'^blogposts/', blogpost_handler),
    )

Now any request coming in to /api/blogpost/some-slug-here/ or /api/blogposts/ will map to BlogpostHandler, with the two different data sets being differentiated in the handler itself. Note that a single handler can be used both for single-object and multiple-object resources. 

.. _anonymous_resources:

Anonymous Resources
===================

Resources can also be "anonymous". What does this mean? This is a special type of resource you can instantiate, and it will be used for requests that aren't authorized (via OAuth, Basic or any authentication handler.)

For example, if we look at our BlogpostHandler from earlier, it might be interesting to offer anonymous access to posts, although we don't want to allow anonymous users to create/update/delete posts. Also, we don't want to expose all the fields authorized users see.

This can be done by creating another handler, inheriting AnonymousBaseHandler (instead of BaseHandler.) This also takes care of the heavy lifting for you.

Like so::

    #!python
    
    from piston.handler import AnonymousBaseHandler, BaseHandler
    
    class AnonymousBlogpostHandler(AnonymousBaseHandler):
       model = Blogpost
       fields = ('title', 'content')
    
    class BlogpostHandler(BaseHandler):
       anonymous = AnonymousBlogpostHandler
       # same stuff as before 

You don't need a "proxy handler" subclassing BaseHandler to use anonymous handlers, you can just point directly at an anonymous resource as well.

.. _working_with_models:

-------------------
Working with Models
-------------------

Piston allows you to tie to a model, but does not require it. The benefit you get from doing so, will become obvious when you work with it:

* If you don't override read/create/update/delete it provides sensible defaults (if the method is allowed by ``allow_methods`` of course.)
* You don't have to specify ``fields`` or ``exclude`` (but you still can, they aren't mutually exclusive!)
* By using a model in a handler, Piston will remember your ``fields``/``exclude`` directives and use them in other handlers who return objects of that type (unless overridden.)

As we've seen earlier, tying to a model is as simple as setting the ``model`` class variable on a handler.

Also see: `Why does Piston use fields from previous handlers <http://bitbucket.org/jespern/django-piston/wiki/FAQ#why-does-piston-use-fields-from-previous-handlers>`_

--------------------
Configuring Handlers
--------------------

Handlers can be configured with 4 different variables.


Model
=====

The model to tie to. See :ref:`working_with_models`.

.. _fields_and_exclude:

Fields/Exclude
==============

A list of fields to include or exclude. Accepts nested listing, and follows foreign keys and manytomany fields.
Also accepts compiled regular expressions. E.g.::

    #!python
    import re
    
    class FooHandler(BaseHandler):
        fields = ('title', 'content', ('author', ('username', 'first_name')))
        exclude = ('id', re.compile('^private_'))


If User can access posts via a Many2many/ForeignKey fields then::

    class UserHandler(BaseHandler):
        model = User
        fields = ('name', ('posts', ('title', 'date')))

will show the title and date from a users posts.

To use the default handler for a nested resource specify an empty list of fields::

    class PostHandler(BaseHandler):
        model = Post
        exclude = ('date',)
    
    class UserHandler(BaseHandler):
        model = User
        fields = ('name', ('posts', ()))

This UserHandler shows all fields for all posts for a user excluding the date.

Neither ``fields``, nor ``exclude`` are required, and either one can be used by itself.

Anonymous
=========

A pointer to an alternate anonymous resource. See :ref:`anonymous_resources`

--------------
Authentication
--------------

Piston supports pluggable authentication through a simple interface. It comes with 2 built-in authentication mechanisms, namely ``piston.authentication.HttpBasicAuthentication`` and ``piston.authentication.OAuthAuthentication``. The Basic auth handler is very simple, and you should use this for reference if you want to roll your own. 

**Note**: that using ``piston.authentication.HttpBasicAuthentication`` with apache and mod_wsgi requires you to add the ``WSGIPassAuthorization On`` directive to the server or vhost config, otherwise django-piston cannot read the authentication data from  ``HTTP_AUTHORIZATION`` in ``request.META``. See: http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIPassAuthorization.

An authentication handler is a class, which must have 2 methods: ``is_authenticated`` and ``challenge``. 

``is_authenticated`` will receive exactly 1 argument, a copy of the ``request`` object Django receives. This object will hold all the information you will need to authenticate a user, e.g. ``request.META.get('HTTP_AUTHENTICATION')``.

Upon successful authentication, this function must set ``request.user`` to the correct ``django.contrib.auth.models.User`` object. This allows for subsequent handlers to identify who is logged in.

It must return either True or False, indicating whether the user was logged in.

For cases where authentication fails, is where ``challenge`` comes in. 

``challenge`` will receive no arguments, and must return a ``HttpResponse`` containing the proper challenge instructions. For Basic auth, it will return an empty response, with the header ``WWW-Authenticate`` set, and status code 401. This will tell the receiving end that they need to supply us with authentication.

For anonymous handlers, there is a special class, ``NoAuthentication`` in ``piston.authentication`` that always returns True for ``is_authenticated``.

OAuth
=====

OAuth is the preferred means of authorization, because it distinguishes between "consumers", i.e. the approved application on your end which is using the API. Piston knows and respects this, and makes good use of it, for example when you use the @throttle decorator, it will limit on a per-consumer basis, keeping services operational even if one service has been throttled.

---------------
Form Validation
---------------

Django has an excellent built-in form validation facility, and Piston can make good use of this.

You can decorate your actions with a @validate decorator, which receives 1 required argument, and one optional. The first argument is the form it will use for validation, and the second argument is the place to look for data. For the ``create`` action, this is 'POST' (default), and for ``update``, it's 'PUT'.

For example::

    #!python
    
    from django import forms
    from piston.utils import validate
    from mysite.myapp.models import Blogpost
        
    class BlogpostForm(forms.ModelForm):
        class Meta:
            model = Blogpost
	...

    @validate(BlogpostForm)
    def create(request, ...):
        ...

Or with a normal form::

    #!python
    
    from django import forms
    from piston.utils import validate
    
    class DataForm(forms.Form):
        data = forms.CharField(max_length=128)
        is_private = forms.BooleanField(default=True, required=False)

    ...

    @validate(DataForm, 'PUT')
    def update(...):
        ...

If data sent to an action that is decorated with a @validate action does not pass the forms ``is_clean`` method, Piston will return an error to the client, and will not execute the action. If the validation passes, then the form object is attached to the request object. Thus you can get to the form (and thus the cleaned_data) via ``request.form`` as in this example::

    #!python
    
    @validate(EchoForm, 'GET')
    def read(self, request):
        return {'msg': request.form.cleaned_data['msg']}


----------------------------
Helpers, utils & @decorators
----------------------------

For your convenience, there's a set of helpers and utilities you can use. One of those is ``rc`` from ``piston.utils``. It contains a set of standard returns that you can return from your actions to indicate a certain situation to the client.

Since <<cset 26293e3884f4>>, these return a **fresh** instance of HttpResponse, so you can use something like this::

    #!python
    
    resp = rc.CREATED
    resp.write("Everything went fine!")
    return resp
    
    resp = rc.CREATED
    resp.write("This will not have the previous 'fine' text in it.")
    return resp

This change is backwards compatible, as it overrides ``__getattr__`` to return a new instance rather than a singleton.

==================   ================================   ======================
Variable	     Result	       		    	Description
==================   ================================ 	======================
rc.ALL_OK            200 OK                           	Everything went well.
rc.CREATED           201 Created			Object was created.
rc.DELETED           204 (Empty body, as per RFC2616)	Object was deleted.
rc.BAD_REQUEST       400 Bad Request                    Request was malformed/not understood.
rc.FORBIDDEN         401 Forbidden                   	Permission denied.
rc.NOT_FOUND         404 Not Found                    	Resource not found.
rc.DUPLICATE_ENTRY   409 Conflict/Duplicate           	Object already exists.
rc.NOT_HERE          410 Gone                         	Object does not exist.
rc.NOT_IMPLEMENTED   501 Not Implemented              	Action not available.
rc.THROTTLED         503 Throttled                    	Request was throttled.
==================   ================================ 	======================

----------
Throttling
----------

Sometimes you may not want people to call a certain action many times in a short period of time. Piston allows you to throttle requests on a global basis, effectively denying them access until the throttle has expired.

Piston will respect OAuth (if used) and limit on a per-consumer basis. If OAuth is not used, Piston will resort to the logged in user, and for anonymous requests, it will fall back to the clients IP address.

Throttling can be enabled via the special @throttle decorator. It takes 2 required arguments, and an optional third argument.

The first argument is the number of requests allowed to be made within a certain amount of seconds. The second argument is the number of seconds. The third argument is optional, and should be a string, which will be appended to the cache key, effectively allowing you to do special throttling for a single action, or group several actions together. If omitted, the throttle will be global.

For example::

    #!python
    
    @throttle(5, 10*60)
    def create(...):


This will throttle if the client calls 'create' more than 5 times within 10 minutes.

You can do grouping like so::

    #!python
    
    @throttle(5, 10*60, 'user_writes')
    def create(...):
    
    @throttle(5, 10*60, 'user_writes')
    def update(...):

------------------------
Generating Documentation
------------------------

Chances are, if you intend to publicly expose your API, that you want to supply documentation. Writing documentation is a tedious process, and even more so if you change things in your code.

Luckily, Piston can do a lot of the heavy lifting for you here as well.

In ``piston.doc`` there is a set of methods, allowing you to easily generate documentation using standard Django views and templates.

The function ``generate_doc`` returns a ``HandlerDocumentation`` instance, which has a few methods:

* .model (get_model) returns the name of the handler,
* .doc (get_doc) returns the docstring for the given handler.
* .get_methods returns a list of methods available. The optional keyword argument ``include_defaults`` (False by default) will also include the fallback methods, if you haven't overloaded them. This may be useful if you want to use these, and still include them in your documentation.

``get_methods`` yields a set of ``HandlerMethod``'s which are more interesting:

* .signature (get_signature) will return the methods //signature//, stripping the first two arguments, which are always 'self' and 'request'. The client will not specify these two, so they are not interesting. Takes an optional argument, ``parse_optional`` (default True), which turns keyword arguments defaulting to None into "<optional>".
* .doc (get_doc) returns the docstring for an action, so you should keep your handler/action specific documentation there.
* .iter_args() will yield a 2-tuple with the argument name, and the default argument (or None.) If the default argument //is// None, the default argument will be 'None' (string). This will allow you to distinguish whether there is a default argument (even if it's None), or if it's empty.

For example::

    #!python
    
    from piston.handler import BaseHandler
    from piston.doc import generate_doc
    
    class BlogpostHandler(BaseHandler):
        model = Blogpost
    
        def read(self, request, post_slug=None):
            """
            Reads all blogposts, or a specific blogpost if
            `post_slug` is supplied.
            """
            ...
    
        @staticmethod
        def resource_uri():
            return ('api_blogpost_handler', ['id'])
    
    doc = generate_doc(BlogpostHandler)
    
    print doc.name # -> 'BlogpostHandler'
    print doc.model # -> <class 'Blogpost'>
    print doc.resource_uri_template # -> '/api/post/{id}'
    
    methods = doc.get_methods()
    
    for method in methods:
        print method.name # -> 'read'
        print method.signature # -> 'read(post_slug=<optional>)'
    
        sig = ''
    
        for argn, argdef in method.iter_args():
            sig += argn
    
            if argdef:
                sig += "=%s" % argdef
    
            sig += ', '
    
        sig = sig.rstrip(",")
        
    print sig # -> 'read(repo_slug=None)'
    
Resource URIs
=============

Each resource can have an URI. They can be accessed in the Handler via his .resource_uri() method.

Also read [[FAQ#what-is-a-uri-template|FAQ: What is a URI Template]].

-----
Tests
-----

<<user zerok>> wrote an initial testsuite for Piston, located in tests/. It uses zc.buildout to run the tests, and isolates an environment with Django, etc. The suite comes with two testrunners: tests/bin/test-1.0 and tests/bin/test-1.1 which run the tests against the respective version of Django and are made available after you're finished with the first two steps as described below.

Running the tests is very easy::

    $ python bootstrap.py 
    Creating directory './bin'.
    [snip]
    Generated script './bin/buildout'.
    
    $ ./bin/buildout -v
    Develop: 'tests/..'
    Getting distribution for 'djangorecipe'.
    Got djangorecipe 0.17.3.
    Getting distribution for 'zc.recipe.egg'.
    Got zc.recipe.egg 1.2.2.
    Uninstalling django-1.0.
    Installing django-1.0.
    django: Downloading Django from: http://www.djangoproject.com/download/1.0.2/tarball/
    Generated script './bin/django-1.0'.
    Generated script './bin/test-1.0'.
        
    $ ./bin/test-1.0
    Creating test database...
    [snip]
    ...
    ----------------------------------------------------------------------
    Ran 6 tests in 0.283s
    
    OK
    Destroying test database...


When running buildout make sure to pass it the -v option. There is currently a small problem with djangorecipe, which is used to create the testscripts etc., that causes the script to hang unless you use the "-v" option.

If you'd like to contribute, more tests are always welcome. There is coverage for many of the basic operations, but not 100%.

--------------
Receiving data
--------------

Piston, being layered on HTTP, works well with post-data (form data), but also works well with more expressive formats such as JSON and YAML.

This allows you to receive structured data easily, rather than just key-value pairs. Piston will attempt to deserialize incoming non-form data via a set of "loaders", depending on the Content-type specified by the client.

For example, if we send JSON to a handler giving the content-type "application/json", Piston will do 2 things:

# Place the deserialized data in ``request.data``, and
# Set ``request.content_type`` to ``application/json``. For form data, this will always be None.

You can use it like so (from  `testapp/handlers.py <http://bitbucket.org/jespern/django-piston/src/7042cd328873/tests/test_project/apps/testapp/handlers.py>`_)::

    #!python

        def create(self, request):
            if request.content_type:
                data = request.data
                
                em = self.model(title=data['title'], content=data['content'])
                em.save()
                
                for comment in data['comments']:
                    Comment(parent=em, content=comment['content']).save()
                    
                return rc.CREATED
            else:
                super(ExpressiveTestModel, self).create(request)
    
If we send the following JSON structure into that, it will handle it appropriately::

    #!python
    
    {"content": "test", "comments": [{"content": "test1"}, {"content": "test2"}], "title": "test"}


It should be noted that sending //anything// that deserializes to this handler will also work, so you can send equally formatted YAML or XML, and the handler won't care.

If your handler doesn't accept post data (maybe it requires more verbose data), there's an easy way to require a specific type of data, via the ``utils.require_mime`` decorator.

This decorator takes a list of types it requires, and you can use the shorthand too, like 'yaml', 'json', etc.

There's also a shortcut for requiring 'json', 'yaml', 'xml' and 'pickle' all in one, called 'require_extended'.

E.g.::

    #!python
    class SomeHandler(BaseHandler):
        @require_mime('json', 'yaml')
        def create(...
    
        @require_extended
        def update(...

.. _streaming:

---------
Streaming
---------

Since <<cset b0a1571ff61a>>, Piston supports streaming its output to the client. This is **disabled** per default, for one reason:

* Django's support for streaming breaks with ``ConditionalGetMiddleware`` and ``CommonMiddleware``.

To get around this, Piston ships with two "proxy middleware classes" that won't execute during a streaming scenario, and hence won't look at (and exhaust) the data before sending it to the client. Without these, Django will look at the contents (to figure out E-Tags and Content-Length), and by doing so, the next peek it takes, will result in nothing.

In ``piston.middleware`` there are two classes you can effectively replace these with.

In settings.py::

    #!python
    
    MIDDLEWARE_CLASSES = (
       # ...
        'piston.middleware.ConditionalMiddlewareCompatProxy',
        'piston.middleware.CommonMiddlewareCompatProxy',
       # ...
    )


Remove any mentions of ``ConditionalGetMiddleware`` and ``CommonMiddleware``, or it **won't work**. If you have any other middleware that looks at the content prior to streaming, you can wrap those in the conditional middleware proxy too::

    #!python
    
    from piston.middleware import compat_middleware_factory
    
    class MyMiddleware(...):
        ...
    
    MyMiddlewareCompatProxy = compat_middleware_factory(MyMiddleware)


And then install ``MyMiddlewareCompatProxy`` instead.

-----------------------
Configuration variables
-----------------------

Piston is configurable in a couple of ways, which allows more granular control of some areas without editing the code.

==============================   ==========
Setting                          Meaning
==============================   ==========
settings.PISTON_EMAIL_ERRORS	 If (when) Piston crashes, it will email the administrators a backtrace (like the Django one you see during DEBUG = True)
settings.PISTON_DISPLAY_ERRORS   Upon crashing, will display a small backtrace to the client, including the method signature expected.
settings.PISTON_STREAM_OUTPUT    When enabled, Piston will instruct Django to stream the output to the client, but please read :ref:`streaming` before enabling it.
==============================   ==========
