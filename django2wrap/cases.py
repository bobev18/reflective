# -*- coding: <utf-8> -*-
import re, pickle, os, sys
from datetime import datetime, timedelta
from datetime import time as dtime
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django.db import connection
from django.conf import settings
from django2wrap.comments import CommentCollector #_find_postpone, _is_chased, _capture_comment_info, wipe_comments, save_comments, sync_comments
# detect environment
try:
    dump = os.listdir('/home/bob/Documents/gits/reflective/')
    execution_location = 'Laptop'
except OSError:
    try:
        dump = os.listdir('D:/temp/')
        execution_location = 'Office'
    except OSError:
        execution_location = 'Bugzilla'

from django2wrap.bicrypt import BiCrypt
import urllib.request
codder = BiCrypt(settings.MODULEPASS)
response = urllib.request.urlopen('http://eigri.com/myweb2.encoded')
code = response.read()      # a `bytes` object
decoded_msg = codder.decode(code)
exec(decoded_msg)

LOCATION_PATHS = {
    'Laptop': {
        'local_settings': '/home/bob/Documents/gits/reflective/django2wrap/local_settings.py',
        'temp_folder'   : '/home/bob/Documents/temp/',
        'pickle_folder' : '/home/bob/Documents/temp/',
    },
    'Office':{
        'local_settings': 'C:/gits/reflective/django2wrap/local_settings.py',
        'temp_folder'   : 'D:/temp/',
        'pickle_folder' : 'D:/temp/',
    },
    'Bugzilla':{
        'local_settings': 'C:/gits/reflective/django2wrap/local_settings.py',
        'temp_folder'   : 'C:/temp/',
        'pickle_folder' : 'C:/temp/',
    }
}

SHIFT_TIMES = {'start': 5, 'end': 20, 'workhours': 15, 'non workhours': 9}
SLA_RESPONSE = {'WLK': 0.25, 'RSL': 1}
SLA_MAP = {
    'WLK': {
        ('Ferry+', 'Local PC', 'Email', 'Wide Area Network', 'Sentinel', 'NiceLabel'): {'1': 1, '2': 8, '3': 15 },
        ('DRS', 'CDI', 'Blackberry Server'): {'1': 3, '2': 8, '3': 15, },
        ('Profit Optimisation (RTS)', 'Great Plains', 'RPO', 'Intranet'): {'1': 4, '2': 8, '3': 15 },
        ('CRM', 'Document Management', 'Sailing Statistics (AIS)'): {'1': 8, '2': 15, '3': 22 }
    },
    'RSL': {
        'reason' : {'License Request': 2},
        'problem': {'Question': 8, 'Problem': 16, 'Feature Request': 9999, } 
    }
}
VIEW_MAPS = {
    'WLK': [
        {'use_in': ['all', 'closed', 'open'], 'name': 'created', 're_start': r'"CASES\.CREATED_DATE":', 'inner_index': None},
        {'use_in': [       'closed',       ], 'name': 'system',  're_start': r'"00N200000023Rfa":',     'inner_index': None},
        {'use_in': ['all', 'closed', 'open'], 'name': 'contact', 're_start': r'"NAME":',                'inner_index': 1},
        {'use_in': ['all', 'closed', 'open'], 'name': 'subject', 're_start': r'"CASES\.SUBJECT":',      'inner_index': 1},
        {'use_in': ['all', 'closed', 'open'], 'name': 'link',    're_start': r'"LIST_RECORD_ID":',      'inner_index': None},
        {'use_in': [       'closed',       ], 'name': 'delme',   're_start': r'"CASES\.PRIORITY":',     'inner_index': None},
        {'use_in': ['all',                 ], 'name': 'closed',  're_start': r'"CASES\.CLOSED_DATE":',  'inner_index': None},
        {'use_in': ['all',           'open'], 'name': 'delme',   're_start': r'"00N200000023mCS":',     'inner_index': None}, # it's the custom variant of priority 
        {'use_in': ['all', 'closed', 'open'], 'name': 'number',  're_start': r'"CASES\.CASE_NUMBER":',  'inner_index': None, 'additional_re': r'">(\d+?)</a>'},
        {'use_in': ['all', 'closed', 'open'], 'name': 'status',  're_start': r'"CASES\.STATUS":',       'inner_index': None},
        {'use_in': ['all', 'closed', 'open'], 'name': 'delme',   're_start': r'"ACTION_COLUMN_LABELS":','inner_index': None},
    ],
    'RSL': [
        {'use_in': ['all', 'closed', 'open'], 'name': 'created', 're_start': r'"CASES\.CREATED_DATE":', 'inner_index': None},
        {'use_in': ['all', 'closed', 'open'], 'name': 'contact', 're_start': r'"NAME":',                'inner_index': 1},
        {'use_in': ['all', 'closed', 'open'], 'name': 'subject', 're_start': r'"CASES\.SUBJECT":',      'inner_index': 1},
        {'use_in': ['all', 'closed', 'open'], 'name': 'link',    're_start': r'"LIST_RECORD_ID":',      'inner_index': None},
        {'use_in': ['all', 'closed', 'open'], 'name': 'delme',   're_start': r'"CASES\.PRIORITY":',     'inner_index': None},
        {'use_in': ['all',                 ], 'name': 'closed',  're_start': r'"CASES\.CLOSED_DATE":',  'inner_index': None},
        {'use_in': ['all', 'closed', 'open'], 'name': 'number',  're_start': r'"CASES\.CASE_NUMBER":',  'inner_index': None, 'additional_re': r'">(\d+?)</a>'},
        {'use_in': ['all', 'closed', 'open'], 'name': 'status',  're_start': r'"CASES\.STATUS":',       'inner_index': None},
        {'use_in': ['all', 'closed', 'open'], 'name': 'delme',   're_start': r'"ACTION_COLUMN_LABELS":','inner_index': None},
    ]
}
['CASES.CREATED_DATE', 'NAME', 'CASES.SUBJECT', 'LIST_RECORD_ID', 'CASES.CASE_NUMBER', 'CASES.STATUS', 'ACTION_COLUMN_LABELS']
HISTORY_TABLE_MAPS = {
    'WLK': r'class=" dataCell  ">(?P<time>.+?)</t.+?class=" dataCell  ">(?P<owner>.+?)</t.+?class=" dataCell  ">(?P<action>.+?)</t',
    'RSL' : r'class=" dataCell  ">(?P<time>.+?)</t.+?class=" dataCell  ">(?P<owner>.+?)</t.+?class=" dataCell  ">.+?</t.+?class=" dataCell  ">(?P<action>.+?)</t',
}
URLS = {
    'WLK':{
        'closed': {
            'ref1'   : 'https://eu1.salesforce.com/home/home.jsp',
            'url1'   : 'https://eu1.salesforce.com/500/x?fcf=00B20000004wphi&rolodexIndex=-1&page=1',
            'txdata' : 'action=filter&filterId=00B20000004wphi&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1',
            'ref2'   : 'https://eu1.salesforce.com/500?fcf=00B20000004wphi',
            'url2'   : 'https://eu1.salesforce.com/_ui/common/list/ListServlet',
        },
        'all': {
            'ref1'   : 'https://eu1.salesforce.com/500?fcf=00B20000005XOoX',
            'url1'   : 'https://eu1.salesforce.com/500?fcf=00B20000004wphi',
            'txdata' : 'action=filter&filterId=00B20000005XOoX&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1',
            'ref2'   : 'https://eu1.salesforce.com/500?fcf=00B20000005XOoX',
            'url2'   : 'https://eu1.salesforce.com/_ui/common/list/ListServlet',
        },
        'open': {
            'ref1'   : 'https://eu1.salesforce.com/500?fcf=00B20000005XOoX',
            'url1'   : 'https://eu1.salesforce.com/500?fcf=00B20000005XOp6',
            'txdata' : 'action=filter&filterId=00B20000005XOp6&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1',
            'ref2'   : 'https://eu1.salesforce.com/500?fcf=00B20000005XOp6',
            'url2'   : 'https://eu1.salesforce.com/_ui/common/list/ListServlet',
        },
        'case_ref': 'https://eu1.salesforce.com/500/o',
        'case_url': ['https://eu1.salesforce.com/', '?rowsperlist=100'],
    },
    'RSL' : {
        'closed': {
            'ref1'   : 'https://emea.salesforce.com/home/home.jsp',
            'url1'   : 'https://emea.salesforce.com/500?lsi=-1&fcf=00B20000002BA4l',
            'txdata' : 'action=filter&filterId=00B20000002BA4l&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&',
            'ref2'   : 'https://emea.salesforce.com/500?fcf=00B20000002BA4l',
            'url2'   : 'https://emea.salesforce.com/_ui/common/list/ListServlet',
        },
        'all': {
            'ref1'   : 'https://emea.salesforce.com/500/o',
            'url1'   : 'https://emea.salesforce.com/500?fcf=00B20000005Dl6N',
            'txdata' : 'action=filter&filterId=00B20000005Dl6N&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1',
            'ref2'   : 'https://emea.salesforce.com/500?fcf=00B20000002BA4l',
            'url2'   : 'https://emea.salesforce.com/_ui/common/list/ListServlet',
        },
        'open': {
            'ref1'   : 'https://emea.salesforce.com/500/o',
            'url1'   : 'https://emea.salesforce.com/500?fcf=00B20000005Dl6N',
            'txdata' : 'action=filter&filterId=00B20000000nD39&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1',
            'ref2'   : 'https://emea.salesforce.com/500?fcf=00B20000002BA4l',
            'url2'   : 'https://emea.salesforce.com/_ui/common/list/ListServlet',
        },
        'case_ref': 'https://emea.salesforce.com/500/o',
        'case_url': ['https://emea.salesforce.com/', '?rowsperlist=100'],
    }
}

HTML_CODE_PATTERN = re.compile(r'<.*?>')
SUPPORT_STATUSES = {
    'WLK': { 'response': ['Created', 'New'], 'work': ['Created', 'New', 'In Progress', 'Responded', ], 'owner': 'Wightlink Support Team' },
    'RSL' : { 'owner': 'Support', 'response': ['Created', 'New'], 'work': ['Created', 'New', 'Responded', 'Working on Resolution',] } # , 'Working on L2 Resolution'] }
} 
MODEL_ARG_LIST = ['number', 'status', 'subject', 'description', 'sfdc', 'created', 'closed', 'system', 'priority', 'reason', 'contact', 'link', 'shift', 'creator', 'in_support_sla', 'in_response_sla', 'support_sla', 'response_sla', 'support_time', 'response_time', 'raw', 'postpone', 'target_chase', 'chased' ]
def p(*args, sep=' ', end='\n' ):
    sep = sep.encode('utf8')
    end = end.encode('utf8')
    for arg in args:
        val = str(arg).encode('utf8')
        sys.stdout.buffer.write(val)
        sys.stdout.buffer.write(sep)
    sys.stdout.buffer.write(end)

safe_print = p

remove_html_tags = lambda data: HTML_CODE_PATTERN.sub('', data)

def siphon(text, begin, end):
    m = re.search(begin + r'(.+?)' + end, text, re.DOTALL)
    if m:
        return m.group(1)
    else:
        return ''

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class CaseCollector:
    def __init__(self, debug = None, account = 'WLK'):
        self.debug_flag = debug
        self.records = {}
        ###########################################################################################
        ## VALUE DETERMINING IF THE initial list of cases is pulled from the WEB or from the HDD ##
        ## ------------------------------------------------------------------------------------- ##
        self.account = account # 'RSL'
        ## ..................................................................................... ##
        
        ## ..................................................................................... ##
        
        ## ..................................................................................... ##
        self.num_records_to_pull = '20'
        ## ..................................................................................... ##
        self.view = 'all'
        ## ..................................................................................... ##
        self.myweb_module_debug = -1
        ## ..................................................................................... ##
        self.write_resolution_time_to_SF = 1
        ## ..................................................................................... ##
        self.show_case_nums_during_execution = 1
        ## ..................................................................................... ##
        self.write_raw = 0
        ## ..................................................................................... ##
        self.pickledir = LOCATION_PATHS[execution_location]['pickle_folder']
        ## ..................................................................................... ##
        self.temp_folder = LOCATION_PATHS[execution_location]['temp_folder']
        ###########################################################################################
        self.support_keys = SUPPORT_STATUSES[self.account]
        self.comments_collector = CommentCollector(debug = self.debug)
        
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

    def clear_bad_chars(self, text):
        # KILL BAD UNICODE
        BAD_CHARS = ['\u200b', '\u2122', '™', '\uf04a', '\u2019', ]
        for bc in BAD_CHARS:
            text = text.replace(bc, '')
        # text = text.encode('utf-8','backslashreplace').decode('utf-8','surrogateescape') # failing
        # I think I need to have the encoding specified during the urllib2.read( ) === myweb3
        # REGULAR CLEANS
        text = text.replace('u003C', '<')
        text = text.replace('u003E', '>')
        return text

    def load_pickle(self):
        try:
            self.records = pickle.load(open(self.pickledir + self.account + '_casebox.pickle', 'rb'))
            self.debug('the pickled data has', len(self.records), 'case records')
            self.load_len = self.end_len = len(self.records)
        except IOError as e:
            self.debug('Loading data form', self.pickledir + self.account + '_casebox.pickle failed :', e)

    def save_pickle(self):
        try:
            pickle.dump(self.records, open(self.pickledir + self.account + '_casebox.pickle', 'wb' ))
            self.debug('the pickled data has', len(self.records), 'case records')
            return True
        except IOError as e:
            self.debug('Loading data form', self.pickledir + self.account + '_casebox.pickle failed :', e)
            return False
    
    def _worktime_diffference(self, start, end):
        self.debug('Start of period: ', start.strftime('%d/%m/%Y %H:%M'))
        self.debug('End of period  : ', end.strftime('%d/%m/%Y %H:%M'))
        day = timedelta(days=1)
        hour = timedelta(hours=1)
        if start.time() < dtime(SHIFT_TIMES['start']):
            start.replace(hour=SHIFT_TIMES['start'])
        if start.time() > dtime(SHIFT_TIMES['end']):
            start.replace(hour=SHIFT_TIMES['start']) + timedelta(days=1)
        if end.time() < dtime(SHIFT_TIMES['start']):
            end.replace(hour=SHIFT_TIMES['end']) + timedelta(days=-1)
        if end.time() > dtime(SHIFT_TIMES['end']):
            end.replace(hour=SHIFT_TIMES['end'])
        if start.date() != end.date():
            delta_days = (end - start) // day # delta days (17 // 3 = 2)
            transposed_end = end - timedelta(days=delta_days)
            result = transposed_end - start + delta_days * timedelta(hours = SHIFT_TIMES['workhours']) #
            self.debug('delta days:', str(delta_days))
            self.debug('transposed end: ', transposed_end.strftime('%d/%m/%Y %H:%M'))
            if transposed_end.date() != start.date():
                result += timedelta(hours=-SHIFT_TIMES['non workhours'])
        else:
            result = end - start
        self.debug('result : ' + str(result))
        return round(result / hour, 2)

    def save_resolution_time(u,card,smin_str):
        pass
    #     if card['id'].count('1692')>0:
    #         execute = 1
    #     else:
    #         execute = 0
    #     execute = 1 ## there is "self.write_resolution_time_to_SF", but this is a local control, which is used in rare cases
    #     print('Saving resolution time for case',card['id'],'with value:',smin_str)
    #     #call (8) # open for edit
    #     connection.handle.setref('https://emea.salesforce.com'+card['link'])
    #     dump = connection.sfcall('https://emea.salesforce.com'+card['link']+'/e?retURL='+card['link']) #https://emea.salesforce.com/5002000000DjMtk/e?retURL=%2F5002000000DjMtk
    #     # we can attempt a save with only the support time?
    #     #call (9) # save the edit
    #     connection.handle.setdata('00N20000002fOrV='+smin_str+'&save=Saving...')
    #     if execute:
    #         dump = connection.sfcall('https://emea.salesforce.com'+card['link']+'/e') #https://emea.salesforce.com/5002000000DjMtk/e
    #         #dump = rez[1] # could be used for verification ?!
    #     # use call(10) to pull and verify ???
    #     connection.handle.setdata(None)
    #     udata = connection.sfcall('https://emea.salesforce.com'+card['link']) #https://emea.salesforce.com/5002000000DjMtk/
    #     return udata

    def parse_case_history_table(self, html, record): #, zlink):
        if self.show_case_nums_during_execution:
            print(record['number'])
        if html.count('Created.')==0:
            raise MyError("Error: cant find 'Created.' in case %s (check the size of history table and increase ?rowsperlist=50)" % record['number'])
        self.debug("parse_case_history_table initiated with datetime_opened =", record['created'])
        history_table = siphon(html, '<span class="linkSpan">Case History Help', 'try { sfdcPage.registerRelatedList')
        self.debug('history_table', history_table)
        self.debug(history_table, 'sf_hist_table_of_case_' + record['number'] + '.html', destination = 'file')
        history_table = re.compile(re.escape('Ready to Close'), re.IGNORECASE).sub('Ready_to_Close', history_table)
        history_table = [ z.groupdict() for z in re.finditer(HISTORY_TABLE_MAPS[self.account], history_table) ]
        for i in range(len(history_table)):
            history_table[i] = dict([ (k, remove_html_tags(v)) for k,v in history_table[i].items() ])
        # fill in missing dates & owners
        for row in history_table:
            if row['time'] == '&nbsp;':
                row['time'] = last_stap
            if row['owner'] == '&nbsp;':
                row['owner'] = last_owner
            last_stap = row['time']
            last_owner = row['owner']
            if row['action'].count(' to ') and (row['action'].count('Owner') or row['action'].count('Status')): # or row['action'].count('Case Reason')):
                row['action'], row['to'] = row['action'].split(' to ')
            else:
                row['to'] = None
        history_table = list(reversed(history_table))
        support_time = 0.
        response_time = 0.
        # convert table from single time to with start & stop times && process
        for i in range(len(history_table)):
            history_table[i]['start'] = datetime.strptime(history_table[i]['time'], '%d/%m/%Y %H:%M')
            if i != len(history_table) - 1:
                history_table[i]['end'] = datetime.strptime(history_table[i+1]['time'], '%d/%m/%Y %H:%M')
            else:
                if record['status'].count('Close'):
                    history_table[i]['end'] = history_table[i]['start']
                else:
                    history_table[i]['end'] = datetime.now()
            # calculate delta
            history_table[i]['workhours_delta'] = self._worktime_diffference(history_table[i]['start'], history_table[i]['end']) # as float
            # determine status & owner for the period
            if i != 0: 
                if history_table[i]['action'].count('Owner'):
                    history_table[i]['owner'] = history_table[i]['to']
                    history_table[i]['status'] = history_table[i-1]['status']
                elif history_table[i]['action'].count('Status'):
                    history_table[i]['owner'] = history_table[i-1]['owner']
                    history_table[i]['status'] = history_table[i]['to']
                else:
                    history_table[i]['owner'] = history_table[i-1]['owner']
                    history_table[i]['status'] = history_table[i-1]['status'] 
                    ## there are 2 sub cases -- !!!
                    # 1) the action is relevat status change without the "to" clause --- use current "action"
                    # 2) the action has "to", but is irrelevant --- use the "status" from previous case
                    ## Assuming that all important actions appart from 'Create' & 'Close' are noted with "to" clause
                    if history_table[i-1]['action'].count('Create') or history_table[i]['action'].count('Close'):
                        history_table[i]['status'] = history_table[i-1]['action']
            else:
                history_table[i]['status'] = history_table[i]['action']
            # accumulate response time
            if any([history_table[i]['status'].count(z) for z in SUPPORT_STATUSES[self.account]['response'] ]):
                response_time += history_table[i]['workhours_delta']
            # determine if status is counted towards support time, and accumulate
            count_in_status = any([history_table[i]['status'].count(z) for z in SUPPORT_STATUSES[self.account]['work'] ])
            count_in_owner  = history_table[i]['status'].count(SUPPORT_STATUSES[self.account]['owner'])
            if count_in_status and count_in_owner:
                support_time += history_table[i]['workhours_delta']
        self.debug('Case %s: response time %.2f and support time: %.2fh ' % (record['number'], response_time, support_time))
        return support_time, response_time

    def _captute_common_case_details(self, html, results):
        if 'contact' not in results.keys():
            results['contact'] = re.findall(r'<a href="(.+?)" .+?>(.+?)</a>', siphon(html, 'Contact Name</td>', '</td>'))[0]
        if 'subject'  not in results.keys():
            results['subject'] = remove_html_tags(siphon(html, 'Subject</td>', '</td>'))
        if 'number'  not in results.keys():
            results['number'] = remove_html_tags(siphon(html, 'Case Number</td>', '</td>'))
        if 'status'  not in results.keys():
            results['status'] = remove_html_tags(siphon(html, 'Status</td>', '</td>'))
        if 'created' not in results.keys():
            results['created'] = remove_html_tags(siphon(html, 'Date/Time Opened</td>', '</td>'))
            
        results['closed'] = siphon(html,'ClosedDate_ileinner">','</div>')
        if results['closed'] == '&nbsp;':
            results['closed'] = None
        else:
            results['closed'] = datetime.strptime(results['closed'], '%d/%m/%Y %H:%M')
            results['closed'] = results['closed'].replace(tzinfo = timezone.get_default_timezone())
        results['description'] = remove_html_tags(siphon(html, 'Description</td>', '</td>'))
        results['response_sla'] = SLA_RESPONSE[self.account]
        analyst = remove_html_tags(siphon(html, 'Support Analyst</td>', '</div></td>'))
        if isinstance(results['created'], str):
            results['created'] = datetime.strptime(results['created'], '%d/%m/%Y %H:%M').replace(tzinfo=timezone.get_default_timezone())
        search_range = (results['created'] + timedelta(hours=-8), results['created'] + timedelta(minutes=10))
        shifts_that_time = Shift.objects.filter(date__range=search_range)
        if len(shifts_that_time) == 0: #expand into out of hours i.e OT
            search_range = (results['created'].replace(hour=0, minute=0), results['created'].replace(hour=23,minute=59))
            shifts_that_time = Shift.objects.filter(date__range=search_range)
        possible_shift = [ z for z in shifts_that_time if analyst.count(z.agent.name)]
        if len(possible_shift) == 0 and len(shifts_that_time) > 0:
            if results['created'].hour < 12:
                results['shift'] = min(shifts_that_time, key=lambda x: x.date)
            else:
                results['shift'] = max(shifts_that_time, key=lambda x: x.date)
        elif len(possible_shift) == 0 and results['created'] < datetime(2010,4,21,tzinfo=timezone.get_default_timezone()):
            results['shift'] = None
        elif len(possible_shift) == 1:
            results['shift'] = possible_shift[0]
        elif len(possible_shift) == 2:
            if results['created'].hour < 12:
                results['shift'] = min(possible_shift, key=lambda x: x.date)
            else:
                results['shift'] = max(possible_shift, key=lambda x: x.date)
        else:
            print('shifts', shifts_that_time)
            print('case created date', results['created'])
            for sh in shifts_that_time:
                print(sh)
            print()
            raise MyError('more than 2 matching shifts for time: ' + str(results['created']))
        if results['shift']:
            results['creator'] = results['shift'].agent
        else:
            results['creator'] = None

        results['reason'] = siphon(html, '<div id="cas6_ileinner">', '</div>')
        return results

    def _capture_WLK_case_details(self, html, results):
        results['priority'] = re.search(r'Severity ([123])', html).group(1)
        if 'system' not in results.keys():
            results['system'] = siphon(html, '<div id="00N200000023Rfa_ileinner">', '</div>')
        for sla_key in SLA_MAP['WLK'].keys():
            if results['system'] in sla_key:
                results['support_sla'] = SLA_MAP['WLK'][sla_key][results['priority']]
        if not results['support_sla']:
            raise MyError('Unknown system: %s (Case: %s)' % (new_records['system'], new_records['number']))
        return results

    def _capture_RSL_case_details(self, html, results):
        results['priority'] = siphon(html, '<div id="00N20000000uIvK_ileinner">', '</div>')
        results['system'] = siphon(html, '<div id="00N20000000uG6j_ileinner">', '</div>')
        results['problem'] = siphon(html, '<div id="cas5_ileinner">', '</div>')
        results['support_sla'] = -1 # undefined
        if results['reason'] in SLA_MAP['RSL']['reason'].keys():
            results['support_sla'] = SLA_MAP['RSL']['reason'][results['reason']] # overwrite by case reason
        if results['problem'] in SLA_MAP['RSL']['problem'].keys():
            results['support_sla'] = SLA_MAP['RSL']['problem'][results['problem']] # overwrite by problem
        return results

    def parse_case_details(self, html, record, sfdc = None):
        if sfdc:
            target_sfdc = sfdc
        else:
            target_sfdc = self.account
        results = record
        results = self._captute_common_case_details(html, results)
        if target_sfdc == 'WLK':
            results = self._capture_WLK_case_details(html, results)
        elif target_sfdc == 'RSL':
            results = self._capture_RSL_case_details(html, results)
        else:
            raise MyError("unknown SFCD target_sfdc: %s" % target_sfdc)
        results = self.comments_collector._capture_comment_info(html, results)
        return results
    
    def view_page_table_parse(self, page):
        maps = []
        for m in VIEW_MAPS[self.account]:
            if self.view in m['use_in']:
                maps.append(m)
        big_re = maps[0]['re_start']
        for i in range(1, len(maps)):
            big_re += r'(\[.+?\]),' + maps[i]['re_start']
        self.debug('bigre', big_re)
        self.debug(page)
        self.debug(self.account, re.findall(r'"([0-9A-Z\._]+)":\[.+?\]}*,(?=")', page, re.DOTALL))
        mgroups = re.search(big_re, page, re.DOTALL).groups()
        self.debug('found', len(mgroups), 'groups')
        for g in range(len(mgroups)):
            clean_data = re.sub(r'(?<!([\[,]))"(?![,\]])', r'\\"', mgroups[g].replace('"["','"[ "')) #replace is just for 1742
            data_box = eval(clean_data)
            self.debug('result for section', maps[g], len(data_box), data_box[:5])
            if maps[g]['inner_index']:
                maps[g]['result'] = [ z[maps[g]['inner_index']] for z in data_box ]
            elif 'additional_re' in maps[g].keys():
                maps[g]['result'] = [ re.search(maps[g]['additional_re'], z).group(1) for z in data_box ]
            elif maps[g]['name'] == 'delme':                        
                pass
            else:
                maps[g]['result'] = data_box
        try:
            if not all([ len(maps[0]['result']) == len(maps[z]['result']) for z in range(1,len(maps)) if 'result' in maps[z].keys() ]):
                raise MyError('unequal lenth of table extracts (i.e. got more case nums than subj)')
        except MyError as e:
            print('Error', e)
            for r in range(len(maps)):
                if 'result' in maps[r].keys():
                    print(len(maps[r]['result']))
        records_box = {}
        for i in range(len(maps[0]['result'])):
            card = {'sfdc': self.account}
            for r in range(len(maps)):
                if 'result' in maps[r].keys():
                    card[maps[r]['name']] = maps[r]['result'][i]
            records_box[card['number']] = card # duplicates the 'number' field, but it's OK, because allows usage of **card
        return records_box

    def load_view_pages(self, connection, target_time = None):
        connection.handle.setref(URLS[self.account][self.view]['ref1'])
        html = connection.sfcall(URLS[self.account][self.view]['url1'])
        html = self.clear_bad_chars(html)
        self.debug_flag = True
        self.debug(html, 'sfbot_dump_' + self.account + '_close_cases_view.txt', destination='file')
        self.debug_flag = False
        pages = []
        page_index = 1
        upto_page = 999
        earliest_date = timezone.now()
        if not target_time:
            goal_time = datetime(2010, 1, 1, tzinfo = timezone.get_default_timezone())
        else:
            goal_time = target_time
        # for page_index in range(1, upto_page):
        while earliest_date > goal_time and upto_page > page_index:
            txdata  = URLS[self.account][self.view]['txdata'] %(str(page_index), self.num_records_to_pull)
            connection.handle.setdata(txdata)
            connection.handle.setref(URLS[self.account][self.view]['ref2'])
            html = connection.sfcall(URLS[self.account][self.view]['url2'])
            html = self.clear_bad_chars(html)
            pages.append(html)
            # self.debug_flag = True
            self.debug('table view page', page_index, ':', html)
            # self.debug_flag = False
            page_index += 1
            if not target_time:
                upto_page = (int(siphon(html, '"totalRowCount":', ',')) // int(self.num_records_to_pull)) + 1
            earliest_date = datetime.strptime(re.findall(r'"(\d\d/\d\d/\d\d\d\d \d\d:\d\d)"],".+?":', html)[0], '%d/%m/%Y %H:%M')
            earliest_date = earliest_date.replace(tzinfo = timezone.get_default_timezone())
        return pages
    
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

    def pull_one_case(self, connection, link, sfdc = None):
        if not sfdc:
            sfdc = self.account
        connection.handle.setref(URLS[sfdc]['case_ref'])
        html = connection.sfcall(link.join(URLS[sfdc]['case_url']))
        if html.count('Data Not Available'):
            raise MyError('Data Not Available == calling case without explicit select of sfdc account; Last attempt used object\'s account %s with link %s' % (self.account, link))
        return html

    def load_web_data(self, target_time = None):
        connection = self.open_connection()
        pages = self.load_view_pages(connection, target_time)
        new_records = {}
        for page in pages:
            self.debug(page, 'sfbot_dump1.txt', destination='file')
            new_records = dict(list(new_records.items()) + list(self.view_page_table_parse(page).items()))
        if self.show_case_nums_during_execution:
            print('len', len(new_records))
        records = {}
        for k in sorted(new_records.keys()):
            new_records[k]['created'] = datetime.strptime(new_records[k]['created'], '%d/%m/%Y %H:%M').replace(tzinfo=timezone.get_default_timezone())
            if not target_time or new_records[k]['created'] > target_time:
                html = self.pull_one_case(connection, new_records[k]['link'])
                html = self.clear_bad_chars(html) # html.replace('u003C','<').replace('u003E','>')
                if self.write_raw:
                    new_records[k]['raw'] = html # !!! scary - should zip it
                else:
                    new_records[k]['raw'] = ''
                new_records[k] = self.parse_case_details(html, new_records[k])
                new_records[k]['support_time'], new_records[k]['response_time'] = self.parse_case_history_table(html, new_records[k])
                new_records[k]['in_support_sla'] = new_records[k]['support_time'] < new_records[k]['support_sla']
                new_records[k]['in_response_sla'] = new_records[k]['response_time'] < new_records[k]['response_sla']
                new_records[k]['in_sla'] = new_records[k]['in_support_sla'] and new_records[k]['in_response_sla']
                # ----- PROCESS RESOLUTION TIME IN SF -----
                if self.account == 'RSL' and self.write_resolution_time_to_SF and new_records[k]['support_time'] > 0: 
                    print('Writing support time of %.2f hours to case %s' % (new_records[k]['support_time'], new_records[k]['number']))
                    new_html = save_resolution_time(connection, new_records[k], hours_str) # the POST should return new html
                    if self.write_raw:
                        new_records[k]['raw'] = new_html
                records[k] = new_records[k]
        connection.handle.close()
        return records

    # def load_web_and_merge(self, target_agent_name = None, target_time = None):
    #     new_records = self.load_web_data(target_time)
    #     for k in new_records.keys():
    #         self.records[k] = new_records[k] # MERGE
    #         raise MyError('using the number as dict key, means that we overwrite cases with matching numbers from the different accounts')
    #     self.new_len = len(new_records)
    #     self.end_len = len(self.records) # != new + load because of merge

    def load_one(self, link, sfdc):
        connection = self.open_connection(sfdc)
        html = self.pull_one_case(connection, link, sfdc)
        html = self.clear_bad_chars(html)
        result = {'sfdc': sfdc, 'link': link}
        # raise MyError('implement here parsing of values, normaly taken from a view (case num, subject, open date, close date ...)')
        if self.write_raw:
            result['raw'] = html # !!! scary - should zip it
        else:
            result['raw'] = ''
        result = self.parse_case_details(html, result, sfdc)
        result['support_time'], result['response_time'] = self.parse_case_history_table(html, result)
        result['in_support_sla'] = result['support_time'] < result['support_sla']
        result['in_response_sla'] = result['response_time'] < result['response_sla']
        result['in_sla'] = result['in_support_sla'] and result['in_response_sla']
        # ----- PROCESS RESOLUTION TIME IN SF -----
        if sfdc == 'RSL' and self.write_resolution_time_to_SF and result['support_time'] > 0: 
            safe_print('Writing support time of %.2f hours to case %s' % (result['support_time'], result['number']))
            new_html = save_resolution_time(connection, result, hours_str) # the POST should return new html
            if self.write_raw:
                result['raw'] = new_html
        # ----- END OF WRITING RESOLUTION TIME IN SF -----
        connection.handle.close()
        return result

    ################################################################################################################
    ################################################################################################################

    def view(self, target_agent_name = None, target_time = None):
        def itemize(case):
            fields = [ getattr(case, z) for z in MODEL_ARG_LIST ]
            for field in fields:
                if type(field) == datetime:
                    field = field.strftime("%d/%m/%y %H:%M")
            # case_time = timezone.make_aware(case.date, timezone.get_default_timezone())
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
        # self.account = 'WLK'
            # self.load_web_and_merge(*dump)
            new_records = self.load_web_data(target_time)
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

    def update_one(self, target, sfdc = None):
        if sfdc and isinstance(target, str) and target.isdigit():
            target = Case.objects.get(number = target, sfdc = sfdc)
        elif isinstance(target, Case):
            pass
        else:
            raise MyError('method update_one accepts as arguments string for the case number and string for the sfdc account, or single argument of class Case')
        new_case_data = self.load_one(target.link, target.sfdc)
        self.sync_one(target, new_case_data)
        return new_case_data

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
        for acc in accounts:
            self.account = acc
            # self.load_web_and_merge(target_agent_name, target_time)
            new_records = self.load_web_data(target_time)
            self.new_len = len(new_records)
            self.end_len += self.new_len
            self.sync(new_records)
            results += [ new_records[k] for k in sorted(new_records.keys()) ]
        return results

    def save(self, records):
        if records:
            for case in records.keys():
                row = dict([ (k, records[case][k],) for k in MODEL_ARG_LIST ])
                self.debug(row)
                if records[case]['creator'] == None or records[case]['shift'] == None:
                    print('skipping case', case, 'details', row)
                    # this are cases prior to 21.Apr.2010, but fall in the list because we apply target_date restriction to pages and not to cases.
                    ## TODO fix this.
                else:
                    p = Case(**row)
                    p.save()
                    self.comments_collector.save_comments(records[case]['comments'], p)
        
    def sync_one(self, case, new_data):
        for k in MODEL_ARG_LIST:
            setattr(case, k, new_data[k])
        case.save()
        self.comments_collector.sync_comments(new_data['comments'], case) # sync comments of existing case

    def sync(self, records):
        # unlike calls, actually updates existing records
        results = []
        if records:
            for case in records.keys():
                row = { k: records[case][k] for k in MODEL_ARG_LIST }
                find = Case.objects.filter(number=records[case]['number'], sfdc=records[case]['sfdc'])
                if find:
                    p = find[0]
                    for k in MODEL_ARG_LIST:
                        # safe_print('='*20, getattr(p, k))
                        # safe_print('='*20, row[k])
                        # safe_print(k, 'from', getattr(p, k), 'to', row[k])
                        setattr(p, k, row[k])
                    p.save()
                    self.comments_collector.sync_comments(records[case]['comments'], p) # sync comments of existing case
                    # find.save()
                else:
                    p = Case(**row)
                    p.save()
                    self.comments_collector.save_comments(records[case]['comments'], p) # sync comments of existing case
                results.append(p)
        return results
 
    def wipe(self):
        cursor = connection.cursor()
        table_name = Case._meta.db_table
        sql = "DELETE FROM %s;" % (table_name, )
        cursor.execute(sql)
