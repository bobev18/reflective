from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
import django2wrap.views
admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^calculator/$', 'calculator.views.calculator'),
    url(r'^chase/$', 'chasecheck.views.chase'),
    url(r'^chase/last_chase_ruslts.html', 'chasecheck.views.results'),
    url(r'^$', django2wrap.views.homepage, name='homepage'),
    url(r'^escalation/$', django2wrap.views.escalation_form, name='escalation form'),
    url(r'^license/$', django2wrap.views.license_form, name='license form'),
    url(r'^listen/$', django2wrap.views.listen, name='license form'),
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