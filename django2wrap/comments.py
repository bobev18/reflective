# -*- coding: <utf-8> -*-
import re #, pickle, os, sys
from datetime import datetime, timedelta
import django.utils.timezone as timezone
# from django2wrap.models import Agent, Shift, Call, Resource, Case, Comment
from django2wrap.models import Comment
from django.db import connection

HTML_CODE_PATTERN = re.compile(r'<.*?>')

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def siphon(text, begin, end):
    m = re.search(begin + r'(.+?)' + end, text, re.DOTALL)
    if m:
        return m.group(1)
    else:
        return ''

class CommentCollector:

    def __init__(self, debug = None):
        self.debug_flag = debug
        
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

    def _find_postpone(self, text):
        postpones = re.finditer(r'resume chas(e|ing)( on){0,1} {0,2}(?P<day>\d\d).(?P<month>\d\d).(?P<year>\d\d\d\d)', text, flags=re.IGNORECASE)
        postpones = [ { k: int(z.groupdict()[k]) for k in z.groupdict().keys() } for z in postpones ]
        if len(postpones) > 0:
            return datetime(tzinfo=timezone.get_default_timezone(), **postpones[0])
        else:
            return None

    def _find_target_chase(self, results):
        now = timezone.now()
        if now.weekday() == 5: #if it's Saturday
            target_time = now - timedelta(days = 1)
        elif now.weekday() == 6: # if it's Sunday
            target_time = now - timedelta(days = 2)
        else:
            target_time = now
        target_time = target_time.replace(hour = 0, minute = 0, second=0, microsecond=0)
        #for card in bigbox:
        # push back chase based on 'Logged as Defect'
        if results['status'] == 'Logged as Defect':
            last_wednesday = target_time - timedelta(days = (target_time.weekday() - 2) % 7)
            target_time = last_wednesday
        return target_time.replace(tzinfo=timezone.get_default_timezone())

    def _is_chased(self, results):
        if results['status'].count('Close'):
            return True
        else:
            chased = False
            if len(results['comments']) > 0:
                comment = results['comments'][0] ## the latest comment
                # comment_time = datetime.strptime(comment['added'], '%d/%m/%Y %H:%M')
                if results['postpone']: # case's postpone should always match comment's
                    chased = results['postpone'] > timezone.now()
                else:
                    chased = not comment['byclient'] and comment['added'] > results['target_chase']
            return chased

    def _capture_comment_info(self, html, record):
        results = record
        comment_table = siphon(html, '<th scope="col" class=" zen-deemphasize">Comment</th>', '</table>')
        comment_pattern = re.compile(r'Created By: <a href="(?P<link>.+?)">(?P<user>.+?)</a> \((?P<added>.+?)\).*?</b>(?P<message>.+?)</td></tr>')
        # the ".*?" handles the <public> last modified, whih is given separated by '|'
        comments = [ z.groupdict() for z in comment_pattern.finditer(comment_table) ]
        if len(comments) > 0:
            for i in range(len(comments)):
                comments[i]['added'] = datetime.strptime(comments[i]['added'], '%d/%m/%Y %H:%M')
                comments[i]['added'] = comments[i]['added'].replace(tzinfo=timezone.get_default_timezone())
                comments[i]['message'] = re.sub(r'(\r\n)+', '\n', comments[i]['message'], re.MULTILINE)
                comments[i]['message'] = re.sub(r'(\r<br>)+', '<br>', comments[i]['message'], re.MULTILINE)
                comments[i]['postpone'] = self._find_postpone(comments[i]['message'])
                comments[i]['byclient'] = comments[i]['user'] != 'StressTester Support' and comments[i]['user'] != 'Wightlink Support Team'
                # comments[i]['agent'] = 
                # comments[i]['shift'] = 
                # comments[i]['call'] = 
                comments[i] = { k:comments[i][k] for k in comments[i].keys() if k not in ['user', 'link'] }
            results['postpone'] = comments[0]['postpone'] # case postpone is on, only if the postpone is in the last comment
        else:
            results['postpone'] = None
        results['comments'] = comments
        results['target_chase'] = self._find_target_chase(results)
        results['chased'] = self._is_chased(results) # requires results['target_chase'] to function
        return results

    ################################################################################################################
    ################################################################################################################
    # TO BE IMPLEMENTED
    # def view(self, target_agent_name = None, target_time = None):
    #     return results

    def wipe_comments(self):
        cursor = connection.cursor()
        table_name = Comment._meta.db_table
        sql = "DELETE FROM %s;" % (table_name, )
        cursor.execute(sql)

    def save_comments(self, comments, case):
        if len(comments) > 0:
            for comm in comments:
                self.debug(comm)
                p = Comment(shift=case.shift, case=case, **comm)
                p.save()

    def sync_comments(self, comments, case):
        # pushes to the db, only if the record is not an exact match; used to fill up missing records, whithout touching the old ones.
        #   would fail for matching 'unique' fields -- that needs a special resolve method!
        if len(comments) > 0:
            for comm in comments:
                # find = Comment.objects.filter(case=case, **comm)
                find = Comment.objects.filter(case=case, added=comm['added'])
                if find:
                    p = find[0]
                    for k in comm.keys():
                        # print('\t', '-'*20, getattr(p, k))
                        # print('\t', '-'*20, comm[k])
                        # print('\t', k, 'from', getattr(p, k), 'to', comm[k])
                        setattr(p, k, comm[k])
                    p.shift=case.shift
                    p.case=case
                    # p.save()
                else:
                    p = Comment(shift=case.shift, case=case, **comm)
                p.save()

