# -*- coding: <utf-8> -*-
import os
from datetime import datetime, timedelta
import django.utils.timezone as timezone
# from django.utils.encoding import smart_text ? ?? 
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django.db import connection as dbconnection
from django.conf import settings
import django2wrap.utils as utils
from django2wrap.comments import CommentCollector
from django2wrap.case_connectors import CaseWebReader, CaseWebConnector, CaseDBConnector, ViewWebReader
#### loads myweb2 ####
from django2wrap.bicrypt import BiCrypt
import urllib.request
codder = BiCrypt(settings.MODULEPASS)
response = urllib.request.urlopen('http://eigri.com/myweb2.encoded')
code = response.read()      # a `bytes` object
decoded_msg = codder.decode(code)
exec(decoded_msg)
#### ------------ ####

TZI = timezone.get_default_timezone()
MODEL_ARG_LIST = ['number', 'status', 'subject', 'description', 'sfdc', 'created', 'closed', 'system', 'priority', 'reason', 'contact', 'link', 'shift', 'creator', 'in_support_sla', 'in_response_sla', 'support_sla', 'response_sla', 'support_time', 'response_time', 'postpone', 'target_chase', 'chased' ]

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class CaseCollector:
    def __init__(self, account = 'WLK', view = None, debug = None):
        self.debug_flag = debug
        self.records = {}
        ###########################################################################################
        ## VALUE DETERMINING IF THE initial list of cases is pulled from the WEB or from the HDD ##
        ## ------------------------------------------------------------------------------------- ##
        self.account = account # 'RSL'
        ## ..................................................................................... ##
        if account:
            self.sfdc = [account]
        else:
            self.sfdc = ['WLK', 'RSL']
        ## ..................................................................................... ##
        if view:
            self.view = view
        else:
            # self.view = 'all'
            # I think "open" is used more often
            self.view = 'open'
        ## ..................................................................................... ##
        self.num_records_to_pull = '20'
        ## ..................................................................................... ##
        ## ..................................................................................... ##
        self.myweb_module_debug = -1
        ## ..................................................................................... ##
        self.write_resolution_time_to_SF = 1
        ## ..................................................................................... ##
        self.show_case_nums_during_execution = 1
        ## ..................................................................................... ##
        self.temp_folder = settings.LOCATION_PATHS['temp_folder']
        ## ..................................................................................... ##
        self.comments_collector = CommentCollector(debug = self.debug)
        ###########################################################################################
        
    def debug(self, *args, sep=' ', end='\n', destination=None):
        if self.debug_flag:
            if destination == 'file':
                try:
                    with open(self.temp_folder + args[1], 'w') as f:
                        f.write(args[0])
                except UnicodeEncodeError as e:
                    with open(self.temp_folder + args[1], 'w', encoding = 'utf-8') as f:
                        f.write(args[0])
                    raise MyError('Unicode fail: ' + str(e))
            else:
                print(*args, sep=sep, end=end)

    def open_connection(self, sfdc = None):
        if not sfdc:
            sfdc = self.account
        try:
            os.remove(self.temp_folder + sfdc + '_sfcookie.pickle')   # WHY ????
        except OSError:
            pass
        cheat = {'WLK': 'wlk', 'RSL': 'st'} #these are hardcoded in myweb2
        connection = sfuser(cheat[sfdc])
        connection.setdir(self.temp_folder)
        connection.setdebug(self.myweb_module_debug)
        connection.sflogin()
        return connection

    #name not only for consistency with views.py
    # def update_one(self, target, sfdc, connection = None):
    def update_one(self, sfdc, target = None, link = None, connection = None):
        if sfdc and isinstance(target, str) and target.isdigit():
            try:
                target = Case.objects.get(number = target, sfdc = sfdc)
            except Case.DoesNotExist:
                target = None

        # at this point the target is either None or an instance of Case
        if not target and not link:
            raise MyError('method update_one should have case or link')

        if target and target.sfdc != sfdc:
            raise MyError('method update_one was given target: ' + str(target) + ' which has SFDC: ' + str(target.sfdc) + ', but that doesn\'t match the provided SFDC: ' + sfdc)
        
        clean_up_connection = False
        if not connection:
            clean_up_connection = True
            connection = self.open_connection(sfdc)
        
        if target:
            case_details = CaseWebConnector(target.link, target.sfdc).load(connection)
        else:
            case_details = CaseWebConnector(link, sfdc).load(connection)

        if clean_up_connection:
            connection.handle.close()

        case_details = self.comments_collector._capture_comment_info(case_details['raw_comments'], case_details)
        case_db_writer = CaseDBConnector(target) # will work with target=None
        case_db_writer.save(self.comments_collector, case_details)

        return case_details

    def view(self, target_agent_name = None, target_time = None):
        def itemize(case):
            fields = [ getattr(case, z) for z in MODEL_ARG_LIST ]
            for field in fields:
                if type(field) == datetime:
                    field = field.strftime("%d/%m/%y %H:%M")
            return fields

        find = Case.objects.all()
        if target_agent_name:
            find = find.filter(creator__name = target_agent_name)
        if target_time:
            find = find.filter(created__range = (target_time.replace(hour=0,minute=0),target_time.replace(hour=23,minute=59)))

        results = [ itemize(z) for z in find ]
        results.insert(0,MODEL_ARG_LIST)
        return results

    def reload(self, *dump):
        raise MyError('You\'ll thank me later')
        results = []
        for sys in ['WLK', 'RSL']:
            self.account = sys
            new_records = self.load_web_data()
            self.new_len = len(new_records)
            self.end_len += self.new_len
            self.wipe()
            self.comments_collector.wipe_comments()
            self.save(new_records) # this does save_comments
            results += [ new_records[k] for k in sorted(new_records.keys()) ]
        resource = Resource.objects.get(name = 'cases')
        resource.last_sync = datetime.now()
        resource.save()
        return results


    def load_web_data(self, view, period_start, period_end = None):
        connection = self.open_connection()
        view_reader = ViewWebReader(self.account, connection, period_start, period_end, view)        # def __init__(self, sfdc, connection, period_start, period_end = None, view = None):
        proto_records = view_reader.load_pages()
        utils.safe_print('proto_records', proto_records)
        records = {}
        for k in sorted(proto_records.keys()):
            print('updateing case', k)
            records[k] = self.update_one(self.account, target=k, link=proto_records[k]['link'], connection=connection) # does the save to DB too

        connection.handle.close()
        return records

    def update(self, target_agent_name = None, target_time = None, target_sfdc = None, target_view = None):
        results = []
        if target_view:
            self.view = target_view
        else:
            self.view = 'all'
        if target_sfdc:
            accounts = [target_sfdc]
        else:
            accounts = ['WLK', 'RSL']
        if not target_time:
            target_time = datetime(2010,4,20,0,0,0,0,TZI)

        for acc in accounts:
            print('SFDC '*5, '='*5, acc, '='*5, 'SFDC '*5)
            self.account = acc
            # self.load_web_and_merge(target_agent_name, target_time)
            new_records = self.load_web_data(target_view, target_time) # , target_period_end)
            # self.new_len = len(new_records)
            # self.end_len += self.new_len
            self.sync(new_records)
            results += [ new_records[k] for k in sorted(new_records.keys()) ]
        return results

    def save(self, records):
        # unlike calls, actually updates existing records
        results = []
        for record in records.keys():
            case = None
            find = Case.objects.filter(number=records[record]['number'], sfdc=records[record]['sfdc'])
            if find:
                case = Case.objects.get(number=records[record]['number'], sfdc=records[record]['sfdc'])
                # using this instead of find[0] ensures there are no duplicates
            case_db_writer = CaseDBConnector(case)
            case_db_writer.save(self.comments_collector, records[record])
            results.append(case)
        return results

    # this is for consistency of the calls in "views" -- will be refactored
    def sync(self, records):
        self.save(records)
 
    def wipe(self):
        cursor = dbconnection.cursor()
        table_name = Case._meta.db_table
        sql = "DELETE FROM %s;" % (table_name, )
        cursor.execute(sql)
