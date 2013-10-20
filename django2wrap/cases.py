# -*- coding: <utf-8> -*-
import re, pickle, os, sys
from datetime import datetime, timedelta
from datetime import time as dtime
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django.db import connection
from django.conf import settings

# detect environment
try:
    dump = os.listdir('/home/bob/Documents/gits/reflective/')
    execution_location = 'Laptop'
except OSError:
    execution_location = 'Office'

# import myweb2
from chasecheck.bicrypt import BiCrypt
import urllib.request
# import imp
# try:
#     bicrypt = imp.load_source('bicrypt', '/home/bob/Documents/gits/reflective/chasecheck/bicrypt.py')
#     execution_location = 'Laptop'
# except IOError:
#     bicrypt = imp.load_source('bicrypt', 'C:/gits/reflective/chasecheck/bicrypt.py')
#     execution_location = 'Office'
# with open(LOCATION_PATHS[execution_location]['local_settings'], 'rt') as f:
#     module_file = f.read()

# matches = re.findall(r"MODULEPASS = '(.+?)'", module_file)
# codder = BiCrypt(matches[0])
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
    }
}
SYSTEMS = {
    'WLK': ['Ferry+', 'CDI', 'Email', 'Local PC', 'Sentinel', 'DRS', 'Intranet', 'Document Management', 'Blackberry Server', 'CRM', 'Profit Optimisation (RTS)', 'Wide Area Network', 'Great Plains', 'RPO', 'Sailing Statistics (AIS)', 'NiceLabel'],
    'RSL' : ['StressTester', 'Sentinel', 'Load Monitor']
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
CLOSED_VIEW_MAPS = {
    'WLK': [
        {'name': 'created', 're_start': r'"CASES\.CREATED_DATE":', 'inner_index': None},
        {'name': 'system',  're_start': r'"00N200000023Rfa":',     'inner_index': None},
        {'name': 'contact', 're_start': r'"NAME":',                'inner_index': 1},
        {'name': 'subject', 're_start': r'"CASES\.SUBJECT":',      'inner_index': 1},
        {'name': 'link',    're_start': r'"LIST_RECORD_ID":',      'inner_index': None},
        {'name': 'delme',   're_start': r'"CASES\.PRIORITY":',     'inner_index': None},
        {'name': 'number',    're_start': r'"CASES\.CASE_NUMBER":',  'inner_index': None, 'additional_re': r'">(\d+?)</a>'},
        {'name': 'status',  're_start': r'"CASES\.STATUS":',       'inner_index': None},
        {'name': 'delme',   're_start': r'"ACTION_COLUMN_LABELS":','inner_index': None},
    ],
    'RSL': [
        {'name': 'created', 're_start': r'"CASES\.CREATED_DATE":', 'inner_index': None},
        {'name': 'contact', 're_start': r'"NAME":',                'inner_index': 1},
        {'name': 'subject', 're_start': r'"CASES\.SUBJECT":',      'inner_index': 1},
        {'name': 'link',    're_start': r'"LIST_RECORD_ID":',      'inner_index': None},
        {'name': 'delme',   're_start': r'"CASES\.PRIORITY":',     'inner_index': None},
        {'name': 'number',    're_start': r'"CASES\.CASE_NUMBER":',  'inner_index': None, 'additional_re': r'">(\d+?)</a>'},
        {'name': 'status',  're_start': r'"CASES\.STATUS":',       'inner_index': None},
        {'name': 'delme',   're_start': r'"ACTION_COLUMN_LABELS":','inner_index': None},
    ]
}
HISTORY_TABLE_MAPS = {
    'WLK': r'class=" dataCell  ">(?P<time>.+?)</t.+?class=" dataCell  ">(?P<owner>.+?)</t.+?class=" dataCell  ">(?P<action>.+?)</t',
    'RSL' : r'class=" dataCell  ">(?P<time>.+?)</t.+?class=" dataCell  ">(?P<owner>.+?)</t.+?class=" dataCell  ">.+?</t.+?class=" dataCell  ">(?P<action>.+?)</t',
}
URLS = {
    'WLK':{
        'closed_list_ref': 'https://eu1.salesforce.com/home/home.jsp',
        'closed_list_url': 'https://eu1.salesforce.com/500/x?fcf=00B20000004wphi&rolodexIndex=-1&page=1',
        'filter_txdata'  : 'action=filter&filterId=00B20000004wphi&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&vf=undefined&isdtp=null',
        'filter_ref'     : 'https://eu1.salesforce.com/500?fcf=00B20000004wphi',
        'filter_url'     : 'https://eu1.salesforce.com/_ui/common/list/ListServlet',
        'case_ref': 'https://eu1.salesforce.com/500/o',
        'case_url': ['https://eu1.salesforce.com/', '?rowsperlist=100'],
    },
    'RSL' : {
        'closed_list_ref': 'https://emea.salesforce.com/home/home.jsp',
        'closed_list_url': 'https://emea.salesforce.com/500?lsi=-1&fcf=00B20000002BA4l',
                          # action=filter&filterId=00B20000002BA4l&filterType=t&page=1&rowsPerPage=200&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&retURL=%2F500%3Ffcf%3D00B20000002BA4l%26rolodexIndex%3D-1%26page%3D1
        'filter_txdata'  : 'action=filter&filterId=00B20000002BA4l&filterType=t&page=%s&rowsPerPage=%s&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&',
        'filter_ref'     : 'https://emea.salesforce.com/500?fcf=00B20000002BA4l',
        'filter_url'     : 'https://emea.salesforce.com/_ui/common/list/ListServlet',
        'case_ref': 'https://emea.salesforce.com/500/o',
        'case_url': ['https://emea.salesforce.com/', '?rowsperlist=100'],
    }
}
OUT_SLA_VIEW_DETAILS = {
    'WLK': ['system', 'priority'],
    'RSL' : ['reason', 'problem']
}
HTML_CODE_PATTERN = re.compile(r'<.*?>')
SUPPORT_STATUSES = {
    'WLK': { 'response': ['Created', 'New'], 'work': ['Created', 'New', 'In Progress', 'Responded', ], 'owner': 'Wightlink Support Team' },
    'RSL' : { 'owner': 'Support', 'response': ['Created', 'New'], 'work': ['Created', 'New', 'Responded', 'Working on Resolution',] } # , 'Working on L2 Resolution'] }
} 
MODEL_ARG_LIST = ['number', 'status', 'subject', 'description', 'sfdc', 'created', 'closed', 'system', 'priority', 'reason', 'contact', 'link', 'shift', 'creator', 'in_support_sla', 'in_response_sla', 'support_sla', 'response_sla', 'support_time', 'response_time', 'raw', 'postpone', 'target_chase', ]
def p(*args, sep=' ', end='\n' ):
    sep = sep.encode('utf8')
    end = end.encode('utf8')
    for arg in args:
        val = str(arg).encode('utf8')
        sys.stdout.buffer.write(val)
        sys.stdout.buffer.write(sep)
    sys.stdout.buffer.write(end)

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
        ###########################################################################################
        ## VALUE DETERMINING IF THE initial list of cases is pulled from the WEB or from the HDD ##
        ## ------------------------------------------------------------------------------------- ##
        self.source = 'web'
        ## ..................................................................................... ##
        self.target_month = datetime.strftime(datetime.now() + timedelta(days=-30), '/%m/%Y')
        ## ..................................................................................... ##
        self.account = account # 'RSL'
        ## ..................................................................................... ##
        self.num_records_to_pull = '20'
        ## ..................................................................................... ##
        # self.page_back = 'all' # takes int ot the default value 'all'
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
        self.syslabox = {'total': {'count': 0, 'out_sup_sla': 0, 'out_resp_sla':0, 'combined':0}}
        for sys in SYSTEMS[self.account]:
            self.syslabox[sys] = {'count': 0, 'out_sup_sla': 0, 'out_resp_sla':0, 'combined':0}
        self.records = {}
        self.load_len = self.new_len = self.end_len = self.mo_len = 0
        self.month_records = {}
        
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

    def _find_postpone(self, text):
        postpones = re.findall(r'resume chas(e|ing)( on){0,1} {0,2}(?P<day>\d\d).(?P<month>\d\d).(?P<year>\d\d\d\d)', text, flags=re.IGNORECASE)
        if len(postpones) > 0:
            return datetime(**postpones[0].groupdict())
        else:
            return None

    def _find_target_chase(self, case):
        now = datetime.now()
        if now.weekday() == 5: #if it's Saturday
            target_time = now - timedelta(days = 1)
        elif now.weekday() == 6: # if it's Sunday
            target_time = now - timedelta(days = 2)
        else:
            target_time = now
        target_time = target_time.replace(hour = 0, minute = 0)
        #for card in bigbox:
        # push back chase based on 'Logged as Defect'
        if case['status'] == 'Logged as Defect':
            last_wednesday = target_time - timedelta(days = (target_time.weekday() - 2) % 7)
            target_time = last_wednesday
        return target_time

    def _is_chased(self, case):
        chased = False
        if len(case['comments']) > 0:
            comment = case['comments'][0] ## the latest comment
            comment_time = datetime.strptime(comment['added'], '%d/%m/%Y %H:%M')
            if case['postpone']: # case's postpone should always match comment's
                chased = case['postpone'] > datetime.now()
            else:
                chased = not comment['byclient'] and comment['added'] > case['target_chase']
        return chased

    def _capture_comment_info(self, html, record):
        results = record
        comment_table = parse(html, '<th scope="col" class=" zen-deemphasize">Comment</th>','</table>')
        comment_pattern = re.compile(r'Created By: <a href="(?P<link>.+?)">(?P<user>.+?)</a> \((?P<added>.+?)\).*?</b>(?P<message>.+?)</td></tr>')
        # the ".*?" handles the <public> last modified, whih is given separated by '|'
        comments = [ z.groupdict() for z in comment_pattern.finditer(comment_table) ]
        if len(comments) > 0:
            for i in range(len(comments)):
                comments[i]['added'] = datetime.strptime(comments[i]['added'], '%d/%m/%Y %H:%M')
                comments[i]['postpone'] = self._find_postpone(comments[i]['message'])
                comments[i]['byclient'] = comments[i]['user'] != 'StressTester Support' and comments[i]['user'] != 'Wightlink Support Team'
                # comments[i]['agent'] = 
                # comments[i]['shift'] = 
                # comments[i]['call'] = 
                comments[i] = { k:comments[i][k] for k in comments[i].keys() if k not in ['user', 'link'] }
        results['comments'] = comments
        ##### next 3 should be in specific order
        results['postpone'] = comments[0]['postpone'] # case postpone is on, only if the postpone is in the last comment
        results['target_chase'] = self._find_target_chase(results)
        results['chased'] = self._is_chased(results)
        return results
    
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
        results['closed'] = datetime.strptime(siphon(html,'ClosedDate_ileinner">','</div>'), '%d/%m/%Y %H:%M')
        results['closed'] = results['closed'].replace(tzinfo = timezone.get_default_timezone())
        results['description'] = remove_html_tags(siphon(html, 'Description</td>', '</td>'))
        results['response_sla'] = SLA_RESPONSE[self.account]
        analyst = remove_html_tags(siphon(html, 'Support Analyst</td>', '</div></td>'))
        results['created'] = datetime.strptime(results['created'], '%d/%m/%Y %H:%M').replace(tzinfo=timezone.get_default_timezone())
        search_range = (results['created'] + timedelta(hours=-8), results['created'] + timedelta(minutes=10))
        shifts_that_time = Shift.objects.filter(date__range=search_range)
        if len(shifts_that_time) == 0: #expand into out of hours i.e OT
            # print('shifts1', shifts_that_time)
            search_range = (results['created'].replace(hour=0, minute=0), results['created'].replace(hour=23,minute=59))
            # print('range', search_range)
            shifts_that_time = Shift.objects.filter(date__range=search_range)
            # print('shifts2', shifts_that_time)
        possible_shift = [ z for z in shifts_that_time if analyst.count(z.agent.name)]
        if len(possible_shift) == 0 and len(shifts_that_time) > 0:
            if results['created'].hour < 12:
                results['shift'] = min(shifts_that_time, key=lambda x: x.date)
            else:
                results['shift'] = max(shifts_that_time, key=lambda x: x.date)
        elif len(possible_shift) == 1:
            results['shift'] = possible_shift[0]
        elif len(possible_shift) == 2:
            if results['created'].hour < 12:
                results['shift'] = min(possible_shift, key=lambda x: x.date)
            else:
                results['shift'] = max(possible_shift, key=lambda x: x.date)
        else:
            for sh in shifts_that_time:
                print(sh)
            raise MyError('more than 2 matching shifts for time: ' + str(results['created']))
        results['creator'] = results['shift'].agent
        results['reason'] = siphon(html, '<div id="cas6_ileinner">', '</div>')
        return results

    def _capture_WLK_case_details(self, html, results):
        results['priority'] = re.search(r'Severity ([123])', html).group(1)
        for sla_key in SLA_MAP[self.account].keys():
            if results['system'] in sla_key:
                results['support_sla'] = SLA_MAP[self.account][sla_key][results['priority']]
        if not results['support_sla']:
            raise MyError('Unknown system: %s (Case: %s)' % (new_records['system'], new_records['number']))
        return results

    def _capture_RSL_case_details(self, html, results):
        results['priority'] = siphon(html, '<div id="00N20000000uIvK_ileinner">', '</div>')
        results['system'] = siphon(html, '<div id="00N20000000uG6j_ileinner">', '</div>')
        results['problem'] = siphon(html, '<div id="cas5_ileinner">', '</div>')
        results['support_sla'] = -1 # undefined
        if results['reason'] in SLA_MAP[self.account]['reason'].keys():
            results['support_sla'] = SLA_MAP[self.account]['reason'][results['reason']] # overwrite by case reason
        if results['problem'] in SLA_MAP[self.account]['problem'].keys():
            results['support_sla'] = SLA_MAP[self.account]['problem'][results['problem']] # overwrite by problem
        return results

    def parse_case_details(self, html, record):
        results = record
        results = self._captute_common_case_details(html, results)
        if self.account == 'WLK':
            results = self._capture_WLK_case_details(html, results)
        elif self.account == 'RSL':
            results = self._capture_RSL_case_details(html, results)
        else:
            raise MyError("unknown SFCD self.account :P")
        results = self._capture_comment_info(html, results)
        return results
    
    def view_page_table_parse(self, page):
        maps = CLOSED_VIEW_MAPS[self.account][:]
        big_re = maps[0]['re_start']
        for i in range(1, len(maps)):
            big_re += r'(\[.+?\]),' + maps[i]['re_start']
        mgroups = re.search(big_re, page, re.DOTALL).groups()
        # mgroups = m.groups()
        self.debug('found', len(mgroups), 'groups')
        for g in range(len(mgroups)):
            clean_data = re.sub(r'(?<!([\[,]))"(?![,\]])', r'\\"', mgroups[g].replace('"["','"[ "')) #replace is just for 1742
            data_box = eval(clean_data)
            self.debug('result for section', maps[g], len(data_box), data_box[:5])
            # print('result for section', maps[g], len(data_box), data_box[:5])
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
        connection.handle.setref(URLS[self.account]['closed_list_ref'])
        html = connection.sfcall(URLS[self.account]['closed_list_url'])
        self.debug(html, 'sfbot_dump_' + self.account + '_close_cases_view.txt', destination='file')
        pages = []
        page_index = 1
        upto_page = 999
        earliest_date = datetime.now()
        if not target_time:
            target_time = datetime(2010,1,1)
        # for page_index in range(1, upto_page):
        while earliest_date > target_time and upto_page > page_index:
            txdata  = URLS[self.account]['filter_txdata'] %(str(page_index), self.num_records_to_pull)
            connection.handle.setdata(txdata)
            connection.handle.setref(URLS[self.account]['filter_ref'])
            html = connection.sfcall(URLS[self.account]['filter_url'])
            pages.append(html)
            # self.debug_flag = True
            self.debug('table view page', page_index, ':', html)
            # self.debug_flag = False
            page_index += 1
            if target_time == datetime(2010,1,1):
                upto_page = (int(siphon(html, '"totalRowCount":', ',')) // int(self.num_records_to_pull)) + 1
            earliest_date = datetime.strptime(re.findall(r'"(\d\d/\d\d/\d\d\d\d \d\d:\d\d)"],".+?":', html)[0], '%d/%m/%Y %H:%M')
        return pages
    
    def load_web_data(self, target_time = None):
        try:
            os.remove(self.temp_folder + self.account + '_sfcookie.pickle')   # WHY ????
        except OSError:
            pass
        cheat = {'WLK': 'wlk', 'RSL': 'st'} #these are hardcoded in myweb2
        connection = sfuser(cheat[self.account])
        connection.setdir(self.temp_folder)
        connection.setdebug(self.myweb_module_debug)
        connection.sflogin()
        pages = self.load_view_pages(connection, target_time)
        new_records = {}
        for page in pages:
            # KILL BAD UNICODE:
            page = page.replace('\u200b','?')
            # page = page.encode('utf-8','backslashreplace').decode('utf-8','surrogateescape') # failing
            # I think I need to have the encoding specified during the urllib2.read( ) === myweb3
            self.debug(page, 'sfbot_dump1.txt', destination='file')
            page = page.replace('u003C','<')
            page = page.replace('u003E','>')
            new_records = dict(list(new_records.items()) + list(self.view_page_table_parse(page).items()))
        if self.show_case_nums_during_execution:
            print('len', len(new_records))
        for k in sorted(new_records.keys()):
            connection.handle.setref(URLS[self.account]['case_ref'])
            html = connection.sfcall(URLS[self.account]['case_url'][0] + new_records[k]['link'] + URLS[self.account]['case_url'][1])
            html = html.replace('u003C','<').replace('u003E','>')
            # KILL BAD UNICODE:
            html = html.replace('™','')
            # BAD_CHARS = ['\uf04a',]
            # for ch in BAD_CHARS:
            #     html.replace(ch, '~')
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
            if self.account == 'st' and self.write_resolution_time_to_SF and new_records[k]['support_time'] > 0: 
                print('Writing support time of %.2f hours to case %s' % (new_records[k]['support_time'], new_records[k]['number']))
                new_html = save_resolution_time(connection, new_records[k], hours_str) # the POST should return new html
                if self.write_raw:
                    new_records[k]['raw'] = new_html
        connection.handle.close()
        return new_records

    def load_web_and_merge(self, target_agent_name = None, target_time = None):
        new_records = self.load_web_data(target_time)
        for k in new_records.keys():
            self.records[k] = new_records[k] # MERGE
        self.new_len = len(new_records)
        self.end_len = len(self.records) # != new + load because of merge

    def calculate_monthly(self):
        for k in self.records.keys():
            # THE MONTH FILTERING HAPPENS HERE ------------------------------------
            if self.target_month in self.records[k]['closed']:
                self.syslabox[self.records[k]['system']]['count']        += 1
                self.syslabox[self.records[k]['system']]['out_sup_sla']  += not self.records[k]['in_support_sla']
                self.syslabox[self.records[k]['system']]['out_resp_sla'] += not self.records[k]['in_response_sla']
                self.syslabox[self.records[k]['system']]['combined']     += not self.records[k]['in_sla']
                self.month_records[self.records[k]['number']] = self.records[k]
        for sla_type in ['out_sup_sla', 'out_resp_sla', 'combined']:
            self.syslabox['total'][sla_type] = sum([ self.syslabox[z][sla_type] for z in SYSTEMS[self.account]])
        self.mo_len = len(self.month_records)

    def monthly(self, target_month = None): 
        self.target_month = datetime.strftime(target_month, '/%m/%Y')
        self.calculate_monthly() #generates the stats
        results = ''
        results += "SFDC account: " + self.account + '\n'
        # results += 'number of pages requested:' + self.page_back + '\n'
        results += 'number of records per page:' + self.num_records_to_pull + '\n'
        results += 'Target: all cases closed in:' + self.target_month + '\n'
        results += 'New cases added:' + str(self.new_len) + '\n'
        results += '-------------------------------' + '\n'
        results += "States considered as pending to support: " + str(SUPPORT_STATUSES[self.account]) + '\n'
        for k in sorted(self.month_records.keys()):
            card = self.month_records[k]
            if card['in_sla']:
                results += 'Case: %s\t%s' % (card['number'], card['subject']) + '\n'
            elif not card['in_response_sla']:
                results += 'Case: %s\t%s' %(card['number'], card['subject']) + '\n'
                result += 'System: %s\tPriority: %s\tTarget Response: %.2fh\tActual: %.2fh' %(
                    card[OUT_SLA_VIEW_DETAILS[self.account][0]], card[OUT_SLA_VIEW_DETAILS[self.account][1]],
                    SLA_RESPONSE[self.account], card['response_time'])
                result += '\n'
            else:
                results += 'Case: %s\t%s' %(card['number'], card['subject']) + '\n'
                result += 'System: %s\tPriority: %s\tTarget Response: %.2fh\tActual: %.2fh' %(
                    card[OUT_SLA_VIEW_DETAILS[self.account][0]], card[OUT_SLA_VIEW_DETAILS[self.account][1]],
                    card['support_sla'], card['support_time'])
                result += '\n'
        results += '-------------------------------' + '\n'
        results += 'Cases closed in' + str(self.target_month) + ':' + str(self.mo_len) + '\n'
        if self.mo_len > 0:
            result += "Out of support SLA count :" + str(self.syslabox['total']['out_sup_sla']) + ", which is" + str(100.00*(self.syslabox['total']['out_sup_sla']/self.mo_len)) + "%"
            result += "Out of response SLA count:" + str(self.syslabox['total']['out_resp_sla']) + ", which is" + str(100.00*(self.syslabox['total']['out_resp_sla']/self.mo_len)) + "%"
            results += "Combined Out of SLA      :" + str(100.00*(self.syslabox['total']['combined']/self.mo_len)) + "%" + '\n'
        results += '-------------------------------' + '\n'
        results += "Count OUT_resp OUT_supp  --- system" + '\n'
        for sys in SYSTEMS[self.account]:
            results += str(self.syslabox[sys]['count']) + '\t' + str(self.syslabox[sys]['out_resp_sla']) + '\t' + str(self.syslabox[sys]['out_sup_sla']) + '\t' + 'for system' + '\t' + sys + '\n'
        return results

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
        results = []
        for sys in SYSTEMS.keys():
            self.sfdc = sys
            self.load_web_and_merge()
            resource = Resource.objects.get(name = 'cases')
            resource.last_sync = datetime.now()
            resource.save()
            self.wipe()
            self.save()
            results += [ self.records[k] for k in sorted(self.records.keys()) ]
        return results

    def update(self, target_agent_name = None, target_time = None): # = 
        self.load_web_and_merge(target_agent_name, target_time)
        self.sync()
        return [ self.records[k] for k in sorted(self.records.keys()) ]

    def save_comments(self, comments, case):
        if len(comments) > 0:
            for comm in comments:
                self.debug(comm)
                p = Comment(shift=case.shift, case=case, **comm)
                p.save()

    def sync_comments(self, comments, case):
        # print(case)
        # print(comments)
        # pushes to the db, only if the record is not an exact match; used to fill up missing records, whithout touching the old ones.
        #   would fail for matching 'unique' fields -- that needs a special resolve method!
        if len(comments) > 0:
            for comm in comments:
                find = Comment.objects.filter(case=case, **comm)
                if not find:
                    p = Comment(shift=case.shift, case=case, **comm)
                    p.save()

    def save(self):
        if self.records:
            for case in self.records.keys():
                row = dict([ (k, self.records[case][k],) for k in MODEL_ARG_LIST ])
                self.debug(row)
                p = Case(**row)
                p.save()
                self.save_comments(self.records[case]['comments'], p)
        
    def sync(self):
        # pushes to the db, only if the record is not an exact match; used to fill up missing records, whithout touching the old ones.
        #   would fail for matching 'unique' fields -- that needs a special resolve method!
        results = []
        if self.records:
            for case in self.records.keys():
                write_row = { k: self.records[case][k] for k in MODEL_ARG_LIST }
                filter_row = { k: write_row[k] for k in write_row.keys() if k not in ['postpone', 'target_chase']}
                # remove row differentiation once the postpone fields ate implemented
                find = Case.objects.filter(**filter_row)
                if not find:
                    p = Case(**write_row)
                    p.save()
                    results.append(p)
                    self.save_comments(self.records[case]['comments'], p)   # save comments of a new case
                self.sync_comments(self.records[case]['comments'], find[0]) # sync comments of existing case
 
    def wipe(self):
        cursor = connection.cursor()
        table_name = Case._meta.db_table
        sql = "DELETE FROM %s;" % (table_name, )
        cursor.execute(sql)

    ##################################################################################
    ##################################################################################
    ##################################################################################
    ##################################################################################

    def get_caselist(self, account, connection):
        _pages=[]
        if account == 'wlk':
            for page in range(pages_back):
                # call to POST desired table rows and filter/sorting                                                                                                                                                           retURL=%2F500%3Ffcf%3D00B20000004wphi%26rolodexIndex%3D-1%26page%3D1&isdtp=null
                # clsoed
                txdata = 'action=filter&filterId=00B20000004wphi&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&vf=undefined&retURL=%2F500%3Ffcf%3D00B20000004wphi%26rolodexIndex%3D-1%26page%3D1&isdtp=null'
                # all open
                txdata = 'action=newfilter&filterId=00B20000005XOp6&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=&rolodexIndex=-1&retURL=%2F500%3Ffcf%3D00B20000004wpi7%26rolodexIndex%3D-1%26page%3D1'
                connection.handle.setdata(txdata)
                connection.handle.setref('https://eu1.salesforce.com/500?fcf=00B20000004wphi')
                udata = connection.sfcall('https://eu1.salesforce.com/_ui/common/list/ListServlet') # list of closed cases
                _pages.append(udata)
        elif account == 'st':
            for page in range(pages_back):
                # call to POST desired table rows and filter/sorting
                # view007
                txdata =    'action=filter&filterId=00B20000005EOlZ&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&retURL=%2F500%3Ffcf%00B20000005EOlZ%26rolodexIndex%3D-1%26page%3D1'
                # all open
                txdata = 'action=newfilter&filterId=00B20000000nD39&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&retURL=%2F500%3Ffcf%3D00B20000005EOlZ%26rolodexIndex%3D-1%26page%3D1'
                connection.handle.setdata(txdata)
                connection.handle.setref('https://emea.salesforce.com/500?fcf=00B20000005EOlZ')
                udata = connection.sfcall('https://emea.salesforce.com/_ui/common/list/ListServlet')
                _pages.append(udata)
        else:
            debugit('errror - wrong account identifier: ',account)

        # debugit('len st pages:',len(_pages))
        return _pages

# TODO:
# make view() return instead of print        DONE
# >> test via django                         DONE
# clear unneccessary "if self.debug..."      DONE
# define fields related to other models      DONE
# merge URLS constant                        DONE
# pass South migration                       DONE
# make load, save & sync use the DB          DONE
# review the records fields for consistency  DONE
# implement comments
# add 'open' cases view (and 'all' cases view)
# >> full reload test (not much sense to do it before comments are in place...)
# 
# 
