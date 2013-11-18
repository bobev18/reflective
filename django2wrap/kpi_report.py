# -*- coding: <utf-8> -*-
import re, os, sys
from calendar import monthrange
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django.db.models import Min
from django.conf import settings
from itertools import groupby
from django2wrap.weekly_report import WeeklyReport

LINKS = {
    'WLK': '<a href="https://eu1.salesforce.com/%s" target="_blank">%s</a>',
    'RSL': '<a href="https://emea.salesforce.com/%s" target="_blank">%s</a>',
}
FORMULA = "="
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
        self.methods  = ['number of shifts', 'number of comments', 'number of calls', 'number of emails out', 'number of gtm sessions', 'results from exams', 'callback sop', 'chasing sop', ]
        self.feedback = ['number of L2 cases solved', 'license sop fail', 'escalation sop fail', ]
        self.fields   = ['Agent', 'points'] + self.methods + self.feedback
        self.results = {}
        self.agents = Agent.objects.filter(start__lt=self.end_of_month.date(), end__gt=self.target_month.date())

        self.agent_names = []
        for agent in self.agents:
            self.agent_names.append(agent.name)
            self.results[agent.name] = {'agent': agent}

        self.cases = Case.objects.filter(closed__gt = self.target_month, closed__lt = self.end_of_month)

    def produce(self):
        table_results = [self.fields]
        callback_results, chase_results = self._callback_n_chasing_sops()
        all_period_comments = Comment.objects.filter(added__range=(self.target_month, self.end_of_month))
        print('range',self.target_month, self.end_of_month, 'len', len(all_period_comments))
        for name in self.agent_names:
            print(name)#, [ (z,z.start,z.end) for z in self.agents if z.name==name])
            self.results[name]['number of shifts'] = self._number_of_shifts(self.results[name]['agent'])
            self.results[name]['number of comments'] = self._number_of_comments(self.results[name]['agent'], all_period_comments)
            self.results[name]['number of calls'] = self._number_of_calls(self.results[name]['agent'])
            self.results[name]['number of emails out'] = self._number_of_emails_out()
            self.results[name]['number of gtm sessions'] = self._number_of_gtm_sessions()
            self.results[name]['results from exams'] = 0
            self.results[name]['callback sop'] = len([ z for z in callback_results if z.name == name ])
            self.results[name]['chasing sop'] = len([ z for z in chase_results if z.name == name ])
            # self.results[name]['number of L2 cases solved'] = self._number_of_not_lack_of_knowledge_cases_solved()
            table_results.append([name, 0] + [ self.results[name][z] for z in self.methods ] + [0, 0, 0])

        # print(str(self.results))
        return table_results

    def _number_of_shifts(self, agent):
        return len(Shift.objects.filter(agent=agent, date__range=(self.target_month, self.end_of_month)))

    def _number_of_comments(self, agent, all_period_comments):
        agent_comments = all_period_comments.filter(agent=agent)
        print('agent comms', len(agent_comments))
        agent_comments = all_period_comments.filter(agent__name=agent.name)
        print('name', agent.name, 'proper? agent comms', len(agent_comments))
        return len(agent_comments)

    def _number_of_calls(self, agent):
        # return len(Call.objects.filter(agent=agent, date__range=(self.target_month, self.end_of_month)))
        result = Call.objects.filter(agent=agent, date__range=(self.target_month, self.end_of_month))
        print('calls for agent:', agent.name, 'date__range', (self.target_month, self.end_of_month))
        count=0
        for call in result:
            count+=1
            # print(call.filename)
        print('count', count)
        return count

    def _number_of_emails_out(self):
        return 0
        pass

    def _number_of_gtm_sessions(self):
        return 0
        pass
    
    def _feedback_to_user_within_1h(self, case, all_case_comments):
        created = case.created
        by_agent_comments = all_case_comments.filter(byclient=False).order_by('added')
        first_comm_date = None
        if len(by_agent_comments) > 0:
            first_comm_date = by_agent_comments[0].added
        else:
            first_comm_date = timezone.now()
        done = created + timedelta(hours=1) > first_comm_date
        responsible_shifts = Shift.objects.filter(date__gt=created + timedelta(hours=1-8), date__lt=created + timedelta(hours=1))
        if not done and responsible_shifts:
            print('case', case, 'first_comm_date', first_comm_date, 'created+1', created + timedelta(hours=1))
            for shift in responsible_shifts:
                print('shift', shift)
            return [ z.agent for z in responsible_shifts ]
        else:
            return []

    def _chasing_per(self, case, all_case_comments):
        if case.sfdc == 'RSL':
            responsible_shift = 'morning'
        else:
            responsible_shift = 'late'
        created_date = case.created.replace(hour=0, minute=0, second=0, microsecond=0)
        if case.status.count('Close'):
            close_date = case.closed
        else:
            close_date = timezone.now()
        delta = close_date - created_date
        results = {}
        resume_on = None
        for z in range(delta.days):
            start = created_date + timedelta(days=z)
            end = created_date + timedelta(days=z+1)
            comments_on_that_date = all_case_comments.filter(added__range=(start, end))
            if len(comments_on_that_date):
                for comm in comments_on_that_date:
                    if comm.postpone:
                        resume_on = comm.postpone
                    else:
                        resume_on = None
                if resume_on and (start < resume_on < end):
                    resume_on = None
                # results.append(bool(len(comments_on_that_date)) or resume_on)
                results[start] = (bool(len(comments_on_that_date)) or resume_on)

        chase_results = []
        for date, chased in results.items():
            if not chased:
                print('not chased on', date)
                # determine the agent responsible
                chase_results.append(Shift.objects.filter(date__range=(start, start + timedelta(days=1))).get(tipe=responsible_shift).agent)

        return chase_results

    def _callback_n_chasing_sops(self):
        all_cases_in_period = Case.objects.exclude(closed__lt=self.target_month).exclude(created__gt=self.end_of_month)
        all_cases_callback_results = []
        all_cases_chase_results = []
        for case in all_cases_in_period:
            all_case_comments = Comment.objects.filter(case=case)
            all_cases_callback_results += self._feedback_to_user_within_1h(case, all_case_comments)
            all_cases_chase_results += self._chasing_per(case, all_case_comments)
        return all_cases_callback_results, all_cases_chase_results

    def _number_of_L2_cases_solved(self):
        return 0


