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

Currently making another try with MySQL-Connector-Python. The query for RELEASE SAVEPOINT #id was returning error that there is no such savepoint, so I edited c:/Python32/Lib/site-packages/mysql/connector/connection.py (arround line: 634) as follows:
     
    if query.count(b'RELEASE SAVEPOINT'):
        result = {'insert_id': 0, 'affected_rows': 0, 'field_count': 0, 'warning_count': 0, 'server_status': 2}
        print('\t\tskip this one')
    else:
        result = self._handle_result(the_result)

This got me past, `python manage.py syncdb --all`, has some test in South to check for *autocommit* is available, abd throws:

    Traceback (most recent call last):
      File "manage.py", line 10, in <module>
        execute_from_command_line(sys.argv)
      File "c:\python32\lib\site-packages\django\core\management\__init__.py", line 399, in execute_from_command_line
        utility.execute()
      File "c:\python32\lib\site-packages\django\core\management\__init__.py", line 392, in execute
        self.fetch_command(subcommand).run_from_argv(self.argv)
      File "c:\python32\lib\site-packages\django\core\management\base.py", line 242, in run_from_argv
        self.execute(*args, **options.__dict__)
      File "c:\python32\lib\site-packages\django\core\management\base.py", line 285, in execute
        output = self.handle(*args, **options)
      File "c:\python32\lib\site-packages\south\management\commands\migrate.py", line 111, in handle
        ignore_ghosts = ignore_ghosts,
      File "c:\python32\lib\site-packages\south\migration\__init__.py", line 220, in migrate_app
        success = migrator.migrate_many(target, workplan, database)
      File "c:\python32\lib\site-packages\south\migration\migrators.py", line 232, in migrate_many
        result = migrator.__class__.migrate_many(migrator, target, migrations, database)
      File "c:\python32\lib\site-packages\south\migration\migrators.py", line 307, in migrate_many
        result = self.migrate(migration, database)
      File "c:\python32\lib\site-packages\south\migration\migrators.py", line 132, in migrate
        result = self.run(migration, database)
      File "c:\python32\lib\site-packages\south\migration\migrators.py", line 113, in run
        if not south.db.db.has_ddl_transactions:
      File "c:\python32\lib\site-packages\django\utils\functional.py", line 49, in __get__
        res = instance.__dict__[self.func.__name__] = self.func(instance)
      File "c:\python32\lib\site-packages\south\db\generic.py", line 124, in has_ddl_transactions
        if getattr(connection.features, 'supports_transactions', True):
      File "c:\python32\lib\site-packages\django\utils\functional.py", line 49, in __get__
        res = instance.__dict__[self.func.__name__] = self.func(instance)
      File "c:\python32\lib\site-packages\django\db\backends\__init__.py", line 664, in supports_transactions
        self.connection.leave_transaction_management()
      File "c:\python32\lib\site-packages\django\db\backends\__init__.py", line 318, in leave_transaction_management
        self.set_autocommit(not managed)
      File "c:\python32\lib\site-packages\django\db\backends\__init__.py", line 333, in set_autocommit
        self._set_autocommit(autocommit)
      File "c:\python32\lib\site-packages\django\db\backends\__init__.py", line 263, in _set_autocommit
        raise NotImplementedError
    NotImplementedError

The test of the transactional capabilities of the DB works fine. The `set_autocommit` call is in the `finally` clause of the test, which means it's executed regardless of the test success. The problem is in the "middleware" implementation of the connector -- it seems to be missing some methods like `set_autocommit`, which are required for South to work.

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
 * update of schedule captures the shifts anew, and for each one overwites the DB record. This fails to remove shifts that were previously recorded, and later removed in the sched - i.e. vacations, sick...
 * even after wipe/reload of shifts, some remain because there are other objects linking towards them

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