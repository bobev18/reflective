REFLECTIVE::DJANGO2WRAP
=======================

The purpose of this app is to consolidate different data used by Reflective Support team into one system. The base of project uses Django 1.6 running over python3, and currently utilizes SQLite3 for DB. Currently it collects data from the following sources:
 * Schedule
 * Recorded Calls Storage
 * Case Tracking
Sources to be implemented:
 * Email Server

The app currently provides the following tools:
 * Chase Checker - checks if cases have been chased
 * Weekly Report (incomplete) - provides the base for the weekly report
 * Montly Report (incomplete) - provides the base for the monthly report
 * Escalation Form (incomplete) - assists with following the escalation SOP
 * License Form (incomplete) - assists with following the license SOP

-------------
Django Basics
-------------

##### Structure
Use *urls.py* under django2wrap to link URLs to specific View. The View can be defined as a subroutine under *views.py* (each app can have it's own views.py). The definition of a View subroutine, needs to return "TemplateResponse" based on a Tempate or "HttpResponse" of a rendered HTML. Templates are located under *django2wrap/templates/*, and are saved as an HTML file.

##### Running test webserver
run server as:

    python manage.py runserver 192.168.3.28:8000

pull application at:

    http://192.168.3.28:8000/chase

##### CSRF validation
Since Django 1.3, there is a "Cross Site Request Forgery protection" that validates whether a POST comes from an "valid" form -- that requires template tag `{% csrf_token %}` somewhere within the form in your template. [CSRF verification failed.](http://stackoverflow.com/questions/9692625/csrf-verification-failed-request-aborted-on-django)

##### Usage of South
the first time:

    python manage.py syncdb
    python manage.py schemamigration django2wrap --initial

afterwards:

    python manage.py schemamigration django2wrap --auto
    python manage.py migrate django2wrap

Note: if running syncdb, you get:

    ...
    Not synced (use migrations):
     - south
     - django_extensions
     - django2wrap
    (use ./manage.py migrate to migrate these)

use this command to fix that:

    python manage.py syncdb --all

------------
Dependencies
------------

##### files prvented from sync via .gitingnore
 * reflective/django4r.db.sqlite3
 * reflective/mysqldb.cnf
 * reflective/django2wrap/bicrypt.py
 * reflective/django2wrap/local_settings.py

##### lib(s) accessed over the web
 * myweb2.py

##### packages
 * virtualenv
 * setuptools -- either came with python3.3, or got installed along virtualenv
 * pip -- either came with python3.3, or got installed along virtualenv
 * six (I think it came along python3.3)
 * Django 1.6c1
 * django-extensions
 * South
 * gspread
 * [pytz](https://pypi.python.org/pypi/pytz/)

##### MySQL
For MySQL tested few alternatives:
 * [MySQL connector for py3](https://github.com/clelland/MySQL-for-Python-3) - worked on linux, but not on Win
 * [PyMySQL](https://github.com/PyMySQL/PyMySQL) - had to install manually, as pip install failed, and didn't work in the end
 * [MySQL-Connector-Python](http://dev.mysql.com/downloads/connector/python/) - does not integrate in Django

##### SQLite3 on Win
Initial DB sync requires setup of superuser via prompt. Using SQLite3 on Win caused an issue -- entering any data via the prompt does not register the pressing of Enter.
Fix: replace the "input" method that is imported from "six" in the following files:
 * in file: C:\Python32\Lib\site-packages\django\contrib\auth\management\commands\createsuperuser.py
 * in file: C:\Python32\Lib\site-packages\django\contrib\auth\management\__init__.py

Code used:

    from django.utils.six.moves import input as _failing

    def input(arg):
        return _failing(arg).strip()

-----
TO DO
-----
 * move "detect environmet" snippet to the settings file
 * consolidate CONSTANTS
 * optimize for speed
 * implement unicode encapsulation:
   - read as bytes & decode
   - encode and write as bytes
 * JSONify

-----
Bugs
-----
 * implementation lacks unicode encapsulation, which causes some special characters to fail with encoding error
  - added "safe_print" for debuging
  - added "clear_bad_chars" method in some classes, but it relies on list of characters known as "bad".

--------------------
Gspread module usage
--------------------
Significant part of the code, relies on the following convention:
* the first sheet of the document should be the schedule
* the "datarange" is denoted as excel range, and it should contain the day and month rows
* the second sheet of the document should represent sched colors as values -- that is achieved by a custom script function:

      function TransferBGColor(targetRange) {
        var ss - SpreadsheetApp.getActiveSpreadsheet();
        var sheet - ss.getSheets()[0];
        //Logger.log("range:" + targetRange);
        var range - sheet.getRange(targetRange);
        var bgColors - range.getBackgrounds();

        //var result - ss.getSheets()[1];
        //var targets - result.getRange("B5:C6");
        //targets.setValues(bgColors);
        return bgColors;
      }

* the usage of the script shown above, is just in the top-left cell:

      TransferBGColor("A1:AC119")

-----------
Other
-----------
to be able to access [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/command_ref.html):

    source ~/.profile
    workon dj4