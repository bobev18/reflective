import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'django2wrap.settings'

from django2wrap import views
from django.http import HttpRequest
request = HttpRequest()
request.POST = {'sendit': None}
print('request', request)
x = views.chase(request)
# html = x._container[0]
# print(html)
