from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


# C:\gits\reflective>python manage.py test
# Creating test database for alias 'default'...
# FATAL ERROR - The following SQL query failed: CREATE TABLE "_south_new_django2wrap_resource" ()
# The error was: near ")": syntax error
#  ! Error found during real run of migration! Aborting.

#  ! Since you have a database that does not support running
#  ! schema-altering statements in transactions, we have had
#  ! to leave it in an interim state between migrations.

# ! You *might* be able to recover with:
#  ! The South developers regret this has happened, and would
#  ! like to gently persuade you to consider a slightly
#  ! easier-to-deal-with DBMS (one that supports DDL transactions)
#  ! NOTE: The error which caused the migration to fail is further up.
# Error in migration: django2wrap:0002_auto__del_field_resource_actions
# Traceback (most recent call last):
#   File "c:\python32\lib\site-packages\django\db\backends\util.py", line 53, in execute
#     return self.cursor.execute(sql, params)
#   File "c:\python32\lib\site-packages\django\db\backends\sqlite3\base.py", line 450, in execute
#     return Database.Cursor.execute(self, query, params)
# sqlite3.OperationalError: near ")": syntax error

# The above exception was the direct cause of the following exception:

# Traceback (most recent call last):
#   File "manage.py", line 10, in <module>
#     execute_from_command_line(sys.argv)
#   File "c:\python32\lib\site-packages\django\core\management\__init__.py", line 399, in execute_from_command_line
#     utility.execute()
#   File "c:\python32\lib\site-packages\django\core\management\__init__.py", line 392, in execute
#     self.fetch_command(subcommand).run_from_argv(self.argv)
#   File "c:\python32\lib\site-packages\django\core\management\commands\test.py", line 50, in run_from_argv
#     super(Command, self).run_from_argv(argv)
#   File "c:\python32\lib\site-packages\django\core\management\base.py", line 242, in run_from_argv
#     self.execute(*args, **options.__dict__)
#   File "c:\python32\lib\site-packages\django\core\management\commands\test.py", line 71, in execute
#     super(Command, self).execute(*args, **options)
#   File "c:\python32\lib\site-packages\django\core\management\base.py", line 285, in execute
#     output = self.handle(*args, **options)
#   File "c:\python32\lib\site-packages\south\management\commands\test.py", line 8, in handle
#     super(Command, self).handle(*args, **kwargs)
#   File "c:\python32\lib\site-packages\django\core\management\commands\test.py", line 88, in handle
#     failures = test_runner.run_tests(test_labels)
#   File "c:\python32\lib\site-packages\django\test\runner.py", line 145, in run_tests
#     old_config = self.setup_databases()
#   File "c:\python32\lib\site-packages\django\test\runner.py", line 107, in setup_databases
#     return setup_databases(self.verbosity, self.interactive, **kwargs)
#   File "c:\python32\lib\site-packages\django\test\runner.py", line 279, in setup_databases
#     verbosity, autoclobber=not interactive)
#   File "c:\python32\lib\site-packages\south\hacks\django_1_0.py", line 103, in wrapper
#     return f(*args, **kwargs)
#   File "c:\python32\lib\site-packages\django\db\backends\creation.py", line 339, in create_test_db
#     load_initial_data=False)
#   File "c:\python32\lib\site-packages\django\core\management\__init__.py", line 159, in call_command
#     return klass.execute(*args, **defaults)
#   File "c:\python32\lib\site-packages\django\core\management\base.py", line 285, in execute
#     output = self.handle(*args, **options)
#   File "c:\python32\lib\site-packages\django\core\management\base.py", line 415, in handle
#     return self.handle_noargs(**options)
#   File "c:\python32\lib\site-packages\south\management\commands\syncdb.py", line 103, in handle_noargs
#     management.call_command('migrate', **options)
#   File "c:\python32\lib\site-packages\django\core\management\__init__.py", line 159, in call_command
#     return klass.execute(*args, **defaults)
#   File "c:\python32\lib\site-packages\django\core\management\base.py", line 285, in execute
#     output = self.handle(*args, **options)
#   File "c:\python32\lib\site-packages\south\management\commands\migrate.py", line 111, in handle
#     ignore_ghosts = ignore_ghosts,
#   File "c:\python32\lib\site-packages\south\migration\__init__.py", line 220, in migrate_app
#     success = migrator.migrate_many(target, workplan, database)
#   File "c:\python32\lib\site-packages\south\migration\migrators.py", line 329, in migrate_many
#     result = self.migrate(migration, database)
#   File "c:\python32\lib\site-packages\south\migration\migrators.py", line 133, in migrate
#     result = self.run(migration, database)
#   File "c:\python32\lib\site-packages\south\migration\migrators.py", line 114, in run
#     return self.run_migration(migration, database)
#   File "c:\python32\lib\site-packages\south\migration\migrators.py", line 84, in run_migration
#     migration_function()
#   File "c:\python32\lib\site-packages\south\migration\migrators.py", line 60, in <lambda>
#     return (lambda: direction(orm))
#   File "C:\gits\reflective\django2wrap\migrations\0002_auto__del_field_resource_actions.py", line 12, in forwards
#     db.delete_column('django2wrap_resource', 'actions')
#   File "c:\python32\lib\site-packages\south\db\sqlite3.py", line 239, in delete_column
#     self._remake_table(table_name, deleted=[column_name])
#   File "c:\python32\lib\site-packages\south\db\generic.py", line 47, in _cache_clear
#     return func(self, table, *args, **opts)
#   File "c:\python32\lib\site-packages\south\db\sqlite3.py", line 110, in _remake_table
#     ", ".join(["%s %s" % (self.quote_name(cname), ctype) for cname, ctype in definitions.items()]),
#   File "c:\python32\lib\site-packages\south\db\generic.py", line 282, in execute
#     cursor.execute(sql, params)
#   File "c:\python32\lib\site-packages\django\db\backends\util.py", line 53, in execute
#     return self.cursor.execute(sql, params)
#   File "c:\python32\lib\site-packages\django\db\utils.py", line 99, in __exit__
#     six.reraise(dj_exc_type, dj_exc_value, traceback)
#   File "c:\python32\lib\site-packages\django\utils\six.py", line 490, in reraise
#     raise value.with_traceback(tb)
#   File "c:\python32\lib\site-packages\django\db\backends\util.py", line 53, in execute
#     return self.cursor.execute(sql, params)
#   File "c:\python32\lib\site-packages\django\db\backends\sqlite3\base.py", line 450, in execute
#     return Database.Cursor.execute(self, query, params)
# django.db.utils.OperationalError: near ")": syntax error
