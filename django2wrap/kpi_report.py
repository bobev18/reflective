# -*- coding: <utf-8> -*-
import re, os, sys
from calendar import monthrange
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django.db.models import Min
from django.conf import settings
from itertools import groupby

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

class KPIReport:
    def __init__(self, target_month = None):
        if not target_month or not isinstance(target_month, datetime):
            self.target_month = datetime(timezone.now().year, timezone.now().month - 1, 1, 0, 0, 0)
        elif isinstance(target_month, str):
            self.target_month = datetime.strptime('1' + target_month, '%d/%m/%Y')
        else:
            raise MyError('invalid target month %s' % target_month)
        self.end_of_month = self.target_month + timedelta(days = monthrange(self.target_month.year, self.target_month.month)[1])

        # self.header = ['postponed', 'num', 'subject', 'created', 'created by', 'status', 'informative subject', 'SLA', 'resolution not documented', 'wrong resolution', 'provided solution without understanding', 'acquire user and problem details', 'feedback to user within 1h', 'chasing per', 'provide case num to user', 'user confirmation obtained', 'GTM or RDC used', 'case morphing', 'license SOP', 'support file SOP', 'escalation SOP', 'get ETA SOP', 'high chase', 'bug num', 'bug planned', 'escalation after confirmation chase x3', ]
        self.methods  = ['number of shifts', 'average number of comments per case', 'number of calls', 'number of emails out', 'number of gtm sessions', 'callback sop', 'chasing sop', 'number of not lack of knowledge cases solved']
        # methods_map = {
        #     'number of shifts': ['agent', 'shifts'],
        #     'average number of comments per case':,
        #     'number of calls',
        #     'number of emails out',
        #     'number of gtm sessions',
        #     'call-back sop',
        #     'chasing sop',
        #     'number of not lack of knowledge cases solved'
        # }
        self.feedback = ['results from exams', 'license procedure followed', 'uj troublshoting kpi', ]
        self.fields   = ['agent', 'points'] + self.methods + self.feedback
        self.results = {}
        self.agents = Agent.objects.filter(start__lt=self.end_of_month.date(), end__gt=self.target_month.date())

        self.agent_names = []
        for agent in self.agents:
            self.agent_names.append(agent.name)
            self.results[agent.name] = {'agent': agent}


        self.cases = Case.objects.filter(closed__gt = self.target_month, closed__lt = self.end_of_month)

    def produce(self):
        table_results = [self.fields]
        for name in self.agent_names:
            print(name)#, [ (z,z.start,z.end) for z in self.agents if z.name==name])
            self.results[name]['number of shifts'] = self._number_of_shifts(self.results[name]['agent'])
            self.results[name]['average number of comments per case'] = self._average_number_of_comments_per_case(self.results[name]['agent'])
            self.results[name]['number of calls'] = self._number_of_calls(self.results[name]['agent'])
            self.results[name]['number of emails out'] = self._number_of_emails_out()
            self.results[name]['number of gtm sessions'] = self._number_of_gtm_sessions()
            self.results[name]['callback sop'] = self._callback_sop()
            self.results[name]['chasing sop'] = self._chasing_sop()
            self.results[name]['number of not lack of knowledge cases solved'] = self._number_of_not_lack_of_knowledge_cases_solved()

            table_results.append([name, 0] + [ self.results[name][z] for z in self.methods ] + [0,0,0])

        # print(str(self.results))
        return table_results

    def _number_of_shifts(self, agent):
        return len(Shift.objects.filter(agent=agent, date__range=(self.target_month, self.end_of_month)))

    def _average_number_of_comments_per_case(self, agent):
        comments_by_all_agents = Comment.objects.filter(added__range=(self.target_month, self.end_of_month))
        # print('len comm all', len(comments_by_all_agents))
        case_nums = [ z.case.number for z in comments_by_all_agents ]
        # print ('len cases nums', len(case_nums))
        num_cases_with_comments_in_period = len(set(case_nums))
        # print ('len cases', num_cases_with_comments_in_period)
        # for comm in comments_by_all_agents:
        #     print(comm)

        # print('@'*10)
        agent_comments = comments_by_all_agents.filter(agent=agent)
        print('agent comms', len(agent_comments))
        return len(agent_comments) / num_cases_with_comments_in_period

    def _number_of_calls(self, agent):
        return len(Call.objects.filter(agent=agent, date__range=(self.target_month, self.end_of_month)))

    def _number_of_emails_out(self):
        pass


    def _number_of_gtm_sessions(self):
        pass


    def _callback_sop(self):
        pass


    def _chasing_sop(self):
        pass


    def _number_of_not_lack_of_knowledge_cases_solved(self):
        pass


