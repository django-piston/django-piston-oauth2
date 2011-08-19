.. Django Piston documentation master file, created by
   sphinx-quickstart on Sat Jul 23 19:25:38 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Django Piston's documentation!
=========================================

Get the `latest version (0.2.2) here <http://bitbucket.org/jespern/django-piston/downloads/django-piston-0.2.2.tar.gz>`_.

Read the [[ReleaseNotes|release notes / what's new]] for 0.2.2.

**NEW**: Discussion group `is hosted on Google Groups <http://groups.google.com/group/django-piston>`_.

Development Version
-------------------

The development version is currently ``0.3dev`` in ``django-piston-oauth2`` `here <https://bitbucket.org/jespern/django-piston-oauth2>`_, and this documentation is built with it.

A mini-framework for Django for creating RESTful APIs
-----------------------------------------------------

Piston is a relatively small Django application that lets you\\
create application programming interfaces (API) for your sites.

It has several unique features:

* Ties into Django's internal mechanisms.
* Supports OAuth out of the box (as well as Basic/Digest or custom auth.)
* Doesn't require tying to models, allowing arbitrary resources.
* Speaks JSON, YAML, Python Pickle & XML (and `HATEOAS <http://blogs.sun.com/craigmcc/entry/why_hateoas>`_.)
* Ships with a convenient reusable library in Python
* Respects and encourages proper use of HTTP (status codes, ...)
* Has built in (optional) form validation (via Django), throttling, etc.
* Supports :ref:`streaming <streaming>`, with a small memory footprint.
* Stays out of your way.

**NB**: OAuth ships with piston for now, but you are not required to use it. It simply provides some boilerplate in case you want to use it later (consumer/token models, urls, etc.)

About The Community Repository
------------------------------

With the community repository we want to give new air to this project and create more active community in the development of this great tool.

Installation
------------

The official stable version is ``0.2.2``, the code in the master branch in bitbucket is not currently that, so, take care with the documentation.

There is a second repo of Jesper Noehr: `django-piston-oauth2 <https://bitbucket.org/jespern/django-piston-oauth2>`_ which has recent version of piston with oauth2 support.

The Community repo lives on `Github <https://github.com/django-piston/django-piston-oauth2>`_

Documentation
-------------

.. toctree::
   :maxdepth: 4

   documentation

Fully functional example
------------------------

Examples speak louder than documentation:

 * urls.py::

     #!python
     
     from django.conf.urls.defaults import *
     from piston.resource import Resource
     from piston.authentication import HttpBasicAuthentication
     
     from myapp.handlers import BlogPostHandler, ArbitraryDataHandler
     
     auth = HttpBasicAuthentication(realm="My Realm")
     ad = { 'authentication': auth }
     
     blogpost_resource = Resource(handler=BlogPostHandler, **ad)
     arbitrary_resource = Resource(handler=ArbitraryDataHandler, **ad)
     
     urlpatterns += patterns('',
         url(r'^posts/(?P<post_slug>[^/]+)/$', blogpost_resource), 
         url(r'^other/(?P<username>[^/]+)/(?P<data>.+)/$', arbitrary_resource), 
     )

 * And as for handlers.py::

     #!python
     
     import re
     
     from piston.handler import BaseHandler
     from piston.utils import rc, throttle
     
     from myapp.models import Blogpost
     
     class BlogPostHandler(BaseHandler):
         allowed_methods = ('GET', 'PUT', 'DELETE')
         fields = ('title', 'content', ('author', ('username', 'first_name')), 'content_size')
         exclude = ('id', re.compile(r'^private_'))
         model = Blogpost
     
         @classmethod
         def content_size(self, blogpost):
             return len(blogpost.content)
     
         def read(self, request, post_slug):
             post = Blogpost.objects.get(slug=post_slug)
             return post
     
         @throttle(5, 10*60) # allow 5 times in 10 minutes
         def update(self, request, post_slug):
             post = Blogpost.objects.get(slug=post_slug)
     
             post.title = request.PUT.get('title')
             post.save()
     
             return post
     
         def delete(self, request, post_slug):
             post = Blogpost.objects.get(slug=post_slug)
     
             if not request.user == post.author:
                 return rc.FORBIDDEN # returns HTTP 401
     
             post.delete()
     
             return rc.DELETED # returns HTTP 204
     
     class ArbitraryDataHandler(BaseHandler):
         methods_allowed = ('GET',)
     
         def read(self, request, username, data):
             user = User.objects.get(username=username)
     
             return { 'user': user, 'data_length': len(data) }


And that's all there's to it.

Getting Help
------------

Piston is well documented and has an ever-growing FAQ. Feel free to add entries you find helpful to the FAQ.

Go read the :ref:`documentation`

Contents
--------

.. toctree::
   :maxdepth: 2

   documentation
   faq

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

