# Django imports
import django.test.client as client
import django.test as test
from django.utils.http import urlencode

# Piston imports
from piston.models import Consumer, Token

# 3rd/Python party imports
import httplib2, urllib, cgi

URLENCODED_FORM_CONTENT = 'application/x-www-form-urlencoded'

class TestCase(test.TestCase):
    pass

