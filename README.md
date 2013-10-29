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

python manage.py schemamigration django2wrap --auto
python manage.py migrate django2wrap

to be able to access virtualenvwrapper:
  source ~/.bash_profile
          source ~/.profile
  workon dj4
(http://virtualenvwrapper.readthedocs.org/en/latest/command_ref.html)

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






DEPENDENCIES:

files prvented from sync via .gitingnore
  reflective/django4r.db.sqlite3
  reflective/mysqldb.cnf
  reflective/chasecheck/bicrypt.py
  reflective/django2wrap/local_settings.py

packages
  virtualenv
  (setuptools, pip -- either came with python3.3, or got installed along virtualenv)
  six (I think it came along python3.3)
  Django 1.6c1
  django-extensions
  South
  gspread
  pytz (https://pypi.python.org/pypi/pytz/)

  ?? MySQL connector for py3 from https://github.com/PyMySQL/PyMySQL (had to install manually, as pip install failed)

pip list on Office PC on 29.oct.2013
  virtualenv (1.10.1)
  setuptools (0.9.8)
  pip (1.4)
  six (1.3.0)
  Django (1.6b4)
  django-extensions (1.2.0)
  South (0.8.1)
  gspread (0.1.0)
  pytz (2013.7)
  
  # downwards are packs that were tried, but did not end up being utilized
  elementtree (1.3a3-20070912-preview)
  gdata (2.0.13)
  MySQL-Connector-Python (1.1.1a1)
  pymysql (0.5)
  wsgiref (0.1.2)

  # downwards are packs from the deployment on the 'bugzilla' machine
  django-registration (1.0)
  stevedore (0.11)
  virtualenv-clone (0.2.4)
  wsgiref (0.1.2)

	
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

==================================
**    Notes on the GSPREAD module usage    **
==================================
The 1st sheet of the document should be the schedule
The "datarange" should contain the day and month of the first day noted in the schedule
The 2nd sheet of the document should be capture of the colors into values
  that is done with a custom script function:
      function TransferBGColor(targetRange) {
        var ss = SpreadsheetApp.getActiveSpreadsheet();
        var sheet = ss.getSheets()[0];
        //Logger.log("range:" + targetRange);
        var range = sheet.getRange(targetRange);
        var bgColors = range.getBackgrounds();
        
        //var result = ss.getSheets()[1];
        //var targets = result.getRange("B5:C6");
        //targets.setValues(bgColors);
        return bgColors;
      }

The usage of the script is just in the top-left cell:
    =TransferBGColor("A1:AC119")