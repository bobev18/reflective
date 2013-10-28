from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import django2wrap.views
admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^calculator/$', 'calculator.views.calculator'),
    url(r'^oldchase/$', 'chasecheck.views.chase'),
    url(r'^oldchase/last_chase_ruslts.html', 'chasecheck.views.results'),
    url(r'^chase/$', 'django2wrap.views.chase', {'run_update_before_chase': True}),
    url(r'^chased/$', 'django2wrap.views.chase'),
    url(r'^weekly/$', 'django2wrap.views.weekly'), #, {'run_update_before_chase': True}),
    url(r'^weekly_/$', 'django2wrap.views.weekly', {'run_update_before_chase': False}),
    url(r'^case/(?P<number>\d+?)/(?P<sfdc>WLK|RSL)*$', django2wrap.views.update_case, name='1case'),
    url(r'^$', django2wrap.views.homepage, name='homepage'),
    url(r'^escalation/$', django2wrap.views.escalation_form, name='escalation form'),
    url(r'^license/$', django2wrap.views.license_form, name='license form'),
    url(r'^listen/$', django2wrap.views.listen, name='player'),
    url(r'^listen/(?P<callid>\d+?)/$', django2wrap.views.listen, name='player'),
    url(r'^listen/(?P<agent>\w+?)/(?P<file_name>.+?\.mp3)/$', django2wrap.views.listen, name='player'),
    url(r'^sync/', django2wrap.views.sync, name='sync'),
    # url(r'^dashboard/', django2wrap.views.dashboard, name='dashboard'),
    # (r'^admin/', include('django.contrib.admin.urls')),
    (r'^admin/', include(admin.site.urls)),

    # url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    # url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}, name='logout'),
    # url(r'^feedback/$', 'feedback.views.contact_form', name='contact-form'),
    # url(r'^register/$', 'haikus.views.register', name='register'), # this is the manual creation of registration form
    #(r'^accounts/', include('registration.backends.default.urls')),
    #url(r'^(?P<username>\w+)/$', user_page, name='user-page'),

    # Examples:
    # url(r'^$', 'django2wrap.views.home', name='home'),
    # url(r'^django2wrap/', include('django2wrap.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

)

# from django.conf import settings

# if settings.DEBUG:
#     urlpatterns += patterns('',
#         (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
#         (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
#     )