
FAQ
===

.. toctree::


How do I...
-----------

...

Why does Piston use fields from previous handlers?
--------------------------------------------------

When you create a handler which is tied to a model, Piston will automatically register it (via a metaclass.) Later on, if a handler returns an object of the model's type, and no fields is defined for it, Piston will resort to the fields defined by the model handler.

For example, this handler::

    #!python
    
    class FooHandler(BaseHandler):
        model = Foo
        fields= ('id', 'title')


is tied to 'Foo'. If we later do this::

    #!python
    
    def read(...):
       f = Foo.objects.get(pk=1)
       return { 'foo': f }


Piston will return the 'id' and 'title' fields of 'f'. If this is not what you want, you can define which fields you **do** want::

    #!python
    
    class OtherHandler(BaseHandler):
        fields = ('something', ('foo', ('title', 'content')))
    
        def read(...):
            f = Foo.objects.get(pk=1)
            return { 'foo': f }


Now it will return the 'title' and 'content' properties of 'f' instead of 'id' and 'title'. This nesting can be as deep as you want it to.

If you want to reset both the metaclass register //and// the nested fields, just use ('foo', ()), which means "take everything."
   
Why does Piston leave out the 'id' even if I specify it
-------------------------------------------------------

**NB**: As per <<cset f34e64f08b3e>>, specifying fields in ``fields`` will override their existence in ``exclude``.

Piston has a "sane default" of excluding the ID from models. This is //usually// internal and shouldn't be exposed to the user. There are of course cases where you want to include the 'id' attribute, and you can do that by resetting 'exclude'.
::

    #!python

    class SomeHandler(BaseHandler):
        exclude = ()

If you want to overwrite this default globally, you can do::

    #!python
    
    from piston.handler import BaseHandler, AnonymousBaseHandler
    
    BaseHandler.fields = AnonymousBaseHandler.fields = ()


What is a URI Template
----------------------

[[http://bitworking.org/projects/URI-Templates/|URI Templates]] define how URIs for accessing a Web resource should be made up. Given the following URI Template:

``http://www.yourproject.com/api/post/{id}/``

And the following variable value

``id := 1``

The expansion of the URI Template is:

``http://www.yourproject.com/api/post/1/``

Tips & Tricks
-------------

As noted by Stephan Preeker in [[http://groups.google.com/group/django-piston/browse_thread/thread/1ca2fd1c89f3df4e|this thread on django-piston]], it's possible to invoke the anonymous handler directly from an authenticated handler, like so::

    #!python
    
    class handler( .. ) 
        def read(self, request, id): 
            self.anonymous.read(id=id) 


This works because ``self.anonymous`` points to the anonymous handler, and you can then invoke methods on it directly.

Reporting Bugs
--------------

Use the [[http://bitbucket.org/jespern/django-piston/issues/|issue tracker]].

Who is using Piston
-------------------

Piston is written internally at Bitbucket, and was later open sourced for you to use. We keep our API versioned (by URL), and you can find the latest version on [[http://api.bitbucket.org/]].

If you are using Piston for anything interesting, feel free to add your site here!

* [[http://dpaste.de/|dpaste.de]] uses piston to provide a simple API for pasting snippets from your desktop or TextMate.

*[[http://www.bachigua.com/|bachigua.com]] uses piston to provide an API for our "iGoogle-like" gadget portal (written in Django)

*[[http://urbanairship.com/|Urban Airship]] loves using piston for their APIs, which initially provide easy to use functionality for mobile applications (like iPhone push notifications and in-app purchases).
