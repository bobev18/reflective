# -*- coding: <utf-8> -*-
import re, pickle, os, sys
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from datetime import time as dtime
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django.db.models import Min
# from django.db import connection
from django.conf import settings
import django2wrap.utils as utils

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
    def __init__(self, report_start_date = None):

        # self.header = ['num', 'subject', 'created', 'created by', 'status', 'informative subject', 'SLA', 'resolution not documented', 'wrong resolution', 'provided solution without understanding', 'acquire user and problem details', 'feedback to user within 1h', 'chasing per', 'provide case # to user', 'user confirmation obtained', 'post 3rd party SLA escalation', 'If Local PC, use GTM to view directly', 'escalation for no solution conf', ]
        self.header = ['postponed', ' num', 'subject', 'created', 'created by', 'status', 'informative subject', 'SLA', 'resolution not documented', 'wrong resolution', 'provided solution without understanding', 'acquire user and problem details', 'feedback to user within 1h', 'chasing per', 'provide case num to user', 'user confirmation obtained', 'GTM or RDC used', 'case morphing', 'license SOP', 'support file SOP', 'escalation SOP', 'get ETA SOP', 'high chase', 'bug num', 'bug planned', 'escalation after confirmation chase x3', ]
        self.tinted = ['subject', 'created', 'created by', 'status', 'case morphing', 'license SOP', 'support file SOP' ]
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
        if report_start_date:
            report_end_date = report_start_date + timedelta(days=7)
        else:
            report_end_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            report_start_date = report_end_date - timedelta(days=7)

        print('true working period for the weekly:', report_start_date, report_end_date)
        # self.closed_workset = Case.objects.filter(status__contains = 'Close').filter(closed__range = (report_start_date, report_end_date)).order_by('sfdc', 'number')
        # self.closed_workset += Case.objects.filter(status__contains = 'Close').filter(closed__range = (report_end_date, timezone.now())).order_by('sfdc', 'number')
        self.closed_workset = Case.objects.filter(status__contains = 'Close').filter(closed__range = (report_start_date, timezone.now())).order_by('sfdc', 'number')
        self.open_workset = Case.objects.exclude(status__contains = 'Close').order_by('sfdc', 'number')
        self.tz = timezone.get_current_timezone()
        # print('*'*30)
        # for case in self.open_workset:
        #     print(('*' + case.number.rjust(14,' ') + '|' + case.created.strftime("%d/%m/%Y %H:%M")).ljust(29,' ') + '*')
        print('*'*60)
        for case in self.closed_workset:
            print(('*' + case.number.rjust(14,' ') + ' | ' + case.created.strftime("%d/%m/%Y %H:%M") + '|' + case.closed.strftime("%d/%m/%Y %H:%M")).ljust(49,' ') + '*')
        print('*'*60)
        print()
        self.report_end_date = timezone.make_naive(report_end_date, self.tz).strftime("%d.%m.%Y")
        self.temp_folder = settings.LOCATION_PATHS['temp_folder']

    def _common(self, case):
        ignores = ['Suspended messages in -65 minutes', 'WARNING: only', 'pass reset', 'password reset', 'Request Error count', 'WARNING: No Bookings receved', 'account was locked', 'user locked', 'account is locked']
        # 'user locked '
        return any([case.subject.lower().count(z.lower()) for z in ignores])

    def action(self):
        results = [[]]
        size = None
        for column in self.header:
            if column == 'status':
                size = 60
            if size:
                results[0].append(column)
            else:
                results[0].append((column,'style="width:'+str(size)+'px;"'))

        wlk_results = []
        rsl_results = []
        for workset in [self.open_workset, self.closed_workset]:
            for case in workset:
                if not self._common(case):
                    comments = case.comments()
                    # results.append([ getattr(self, '_' + k.replace(' ', '_'))(case, comments, *self.mapper[k]['attr']) for k in self.header ])
                    result_this_case = []
                    for column in self.header:
                        value = getattr(self, '_' + column.strip().replace(' ', '_'))(case, comments, *self.mapper[column.strip()]['attr'])
                        if column in self.tinted and case.sfdc == 'RSL':
                            value = (value, 'style="background-color:#CCFFFF;"')
                        result_this_case.append(value)

                    if case.sfdc == 'RSL':
                        rsl_results.append(result_this_case)
                    else:
                        wlk_results.append(result_this_case)

        wlk_results.sort(key=lambda x: x[5].count('Close'))
        rsl_results.sort(key=lambda x: x[5].count('Close'))
        results += rsl_results + wlk_results
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
        with open(self.temp_folder+'weekly_'+self.report_end_date+'.csv', 'w', encoding = 'utf-8') as f:
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
        commons = [
            [r'restarted( the)* (Nice.*Label|NPS|NL)( service)*'],  # try against the entire corpus see how many we got; (measure against count'NL' ?)
            ['license request'], 
        ]

        return 'n/a'

    def _wrong_resolution(self, case, comments, *args):
        return 'n/a'

    def _provided_solution_without_understanding(self, case, comments, *args):
        return 'n/a'

    def _acquire_user_and_problem_details(self, case, comments, *args):
        return 'done'

    def _feedback_to_user_within_1h(self, case, comments, *args):
        created = case.created
        bysupport_comments = comments.filter(byclient=False)#.order_by('-added')
        first_comm_date = None
        if len(bysupport_comments) > 0:
            first_comm_date = bysupport_comments[0].added
        else:
            first_comm_date = timezone.now()
        # done = created + timedelta(hours=1) > first_comm_date
        if case.number.count('2276'):
            done = utils.worktime_diffference(created, first_comm_date, True) < 1
        else:
            done = utils.worktime_diffference(created, first_comm_date) < 1
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
            'client': [['close the case'], ['data( has) c(o|a)me through'],['happy to close this case'], ['Please close this case'],['close this one'],['Please close the case'],['You can close the call'],
            ['You can close this call']],
            'agent' : [
                ['called','everything is back online'],
                ['called','printing is ok (today|now)'], #Called Ryde TO, printing is ok today.
                [r'Ferry+ is performing nice and smooth'],
                [r'This solved the problem'],
                [r'problem( is)* solved'],
                ['called', 'TO', 'no issues'],
                ['called', 'TO', 'all fine'],
                # ['called', '*any client here*', str(['all fine', r'everything is back (online|to normal)', r'no( more)* issues', ''])], # this is just for anotation of futute design
                [r'all( (seems|is))* fine'],
                [r'there(\'| i)s no errors*'],
                [r'there(\'| a)re no errors*'],
                [r'confirmed( that)*', ' is fine'],
                [r'(is )*work(s|ing) (fine|again)'],
                [r'(better|ok|works) now'],
                [r'logged in successfully'],
                [r'managed to', 'successfully'],
                [r'agreed( that)*( the)* case can be closed'],
                [r'agreed( to)*', r'close the case'],
                [r'it now seems to work'],
                [r'this case can be closed'],
                [r'that.{1,2}s perfect, thank you'],
                [r'happy to close this case'],
                [r'printing is fine'],
                [r'\. *No problems\.'],
                [r'Got confirmation that they received the email'],
                [r'Thank you for your reply. I am closing the case now'],

                # The printing is fine for the whole office.
                # asked me not to repeat this procedure but to close the case
                # telephone is replaced and they are currently using it
                # is performing nice and smoothly
                # all fine ,no issues
                # everything is back online
                # server is running again. 
                # Confirmed with Pauline Crisp that everything is working
                # everything is OK
                # Called her back the till was working
            ]
        }

        print('='*10, case.number, case.status, '='*10)
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
                safe_print('latest comment', conf_message)
                if comment.byclient: # approval in comment or inline copy of client's email
                    tests = APPROVALS['client']
                else: # phone approval
                    tests = APPROVALS['agent']
                    
                    # all_tests = []
                    # for test in :
                    #     test_expression = r'[^\w]+?'.join(test)
                    #     test_result = re.findall(test_expression, conf_message, re.I)
                    #     if len(test_result):
                    #         success_expression = test_expression
                    #     all_tests.append(len(test_result))
                    # close_conf = any(all_tests)
                all_tests = []
                for test in tests:
                    test_expression = r'.+?'.join(test)
                    test_result = re.findall(test_expression, conf_message, re.I)
                    if len(test_result):
                        success_expression = test_expression
                        safe_print('\t', test_expression)
                        safe_print('\t',test_result)
                    all_tests.append(len(test_result))
                close_conf = any(all_tests)

                if close_conf:                
                    result = '<span title="' + comment.message + ' <<<<< ' + success_expression + '">done</span>'
                else:
                    result = ('<span title="' + comment.message + '">fail</span>', 'style="background-color:#FF0000;"')
            else:
                result = ('fail', 'style="background-color:#FF0000;"')
        return result

    def _GTM_or_RDC_used(self, case, comments, *args):
        big_text = '\n'.join([comm.message for comm in comments])
        GTM_mention = [ len(re.findall(r'[^\w]'+z+r'[^\w]', big_text, re.I)) for z in [r'GTM', r'Go To Meeting', r'GoToMeeting'] ]
        RDC_mention = [ len(re.findall(r'[^\w]'+z+r'[^\w]', big_text, re.I)) for z in [r'RDC', r'Remote Session', r'Remote Desktop'] ]
        # print(case.number, 'GTM len findall per keywords', GTM_mention)
        # print(case.number, 'RDC len findall per keywords', RDC_mention)
        GTM_mention = any(GTM_mention)
        RDC_mention = any(RDC_mention)
        is_used = GTM_mention or RDC_mention
        # should_be_used = False
        # return 'done'*(should_be_used and is_used) + 'n/a'*(not should_be_used) + 'fail'*(should_be_used and not is_used)
        return 'done'*(is_used) + 'fail'*(not is_used)

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
        bugs = re.findall(r'[^\w]bug[^\d]{0,2}(\d+)[^\d]', case.subject, re.I)
        bugs += re.findall(r'[^\w]bug[^\d]{0,2}(\d+)[^\d]', '\n'.join([comm.message for comm in comments]), re.I)
        bugs = ', '.join(bugs)
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


