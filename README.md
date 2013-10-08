django2wrap
===========

In the project "django2wrap" has one app
 - chasecheck

--- == Basic test/use: == --
run server as:
	python manage.py runserver 192.168.3.28:8000
pull application at:
	http://192.168.3.28:8000/chase -- to view the "Ivoke Chase Checker" app

use urls.py under django2wrap to link URLs to specific View
The View can be defined under views.py under the corresponding app
The definition of a View as subroutine, needs to return "TemplateResponse" based on a Tempate
The Template is defined under django2wrap/templates/ as an html file

Note:
Apparently since Django 1.3, there is a "Cross Site Request Forgery protection" that validates whether a POST comes from an "valid" form -- that requires template tag {% csrf_token %} somewhere within the form in your template.
(via http://stackoverflow.com/questions/9692625/csrf-verification-failed-request-aborted-on-django)
"""
This way, the template will render an hidden element with the value set to a token. Django will check that token to validate your POST request.
For more info, check the Django documentation at: https://docs.djangoproject.com/en/1.3/ref/contrib/csrf/
"""

==================================
**    Notes on the CHASE app    **
==================================
The code for chase results is directly copied from daily_chaser.0.74.py
It's restructured a bit to fit in the Views subroutine. Other minor changes were added during troublesooting
myweb2.py lib is accessed over the web

TODOS:
 - There are a lot of hardcoded file locations
   = debug dump files -- should be based on DEBUG_DUMP_LOCATION constant
   = path to the "last run results" -- should use relative path
 - Utilize the Django template language
 
 Bug: some foreign characters cause problems:
  - in the case details/comments caused inability to save the log files -- 
    Commented the dumps of the logs to file at this point - may need to tackle it later.
  - in case subject cause problem displaying the chase page -- 
    Currently the agents should edit the case subject

DEPENDANCY:

	shifts uses gspread
	MySQL connector for py3 from https://github.com/PyMySQL/PyMySQL (had to install manually, as pip install failed)
	
DB issues working on SQLite3:
 - on WinXP does not accept any input that is prompted during creation of superuser;
    to fix, I replaced the "input" method that is imported from "six" as follows:
      in file:       C:\Python32\Lib\site-packages\django\contrib\auth\management\commands\createsuperuser.py:
      and in file:   C:\Python32\Lib\site-packages\django\contrib\auth\management\__init__.py:
      ```
      from django.utils.six.moves import input as _failing

      def input(arg):
          return _failing(arg).strip()
      

 - on XP runing syncdb after addition of south to the installed apps gave:
      ```
      Synced:
       > django.contrib.auth
       > django.contrib.admin
       > django.contrib.contenttypes
       > django.contrib.messages
       > django.contrib.sessions
       > django.contrib.sites
       > django.contrib.staticfiles
       > django.contrib.humanize

      Not synced (use migrations):
       - south
       - django_extensions
       - django2wrap
      (use ./manage.py migrate to migrate these)
 Fix: use
      python manage.py syncdb --all

