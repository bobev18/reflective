import imaplib, email, re, sys, pickle
from datetime import datetime, timedelta, date
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift
from django.conf import settings # import EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

NIKNAMES = { 
    'Rosti'  : ['Rosti', 'Rostislav'],
    'Radi'   : ['Radi', 'Rado', 'Radoslav'], 
    'Niki'   : ['Niki', 'Nikolai'],
    'Miglena': ['Miglena', 'Megi' ],
    'Iliyan' : ['Iliyan'],
    'Juliana': ['Juliana'],
    'Boris'  : ['Boris'],
    'Ivelin' : ['Ivelin'],
}

PICKLE_PATHFILE = 'D:/temp/emails_'

HTML_CODE_PATTERN = re.compile(r'<.*?>')
remove_html_tags = lambda data: HTML_CODE_PATTERN.sub('', data)

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

class EmailCollector:
    def __init__(self, debug=None):
        self.debug = debug
        self.account = None

    def _open_box(self, user, password, host, port):
        # if port == 993:
        #     box = imaplib.IMAP4_SSL(host=host, port=port)
        # else:
        #     box = imaplib.IMAP4(host=host, port=port)
        # print('host',host,"pine")
        # print('port',port,993)
        # mail = imaplib.IMAP4_SSL(host="pine", port=993)
        # mail.login("itsupport", "Wightlink99")
        # print('mail folders', mail.list())
        # exit(1)

        box = imaplib.IMAP4_SSL(host=host, port=port)
        # box.debug = 2
        # print('check', box.status('"Sent Items"',''))
        box.login(user, password)
        # print('mail folders', box.list())
        return box

    def _close_box(self, box):
        box.close()
        box.logout()

    def _get_first_text_block(self, email_message_instance):
        for part in email_message_instance.walk():
            if part.get_content_maintype() == 'text':
                return part.get_payload()

    def _pull_messages(self, box, target_start_date, target_end_date):
        results = []
        for folder in settings.BOX_SPECS[self.account]['sent']:
            print('\tfolder', folder)
            count = 0
            box.select(mailbox=folder, readonly=True)
            since_date = target_start_date.strftime("%d-%b-%Y")
            result, data = box.uid('search', None, '(SENTSINCE {date})'.format(date=since_date))
            all_messages = data[0].split()
            print('all_messages', len(all_messages))
            for uid in all_messages:
                print('uid::', uid)
                result, data = box.uid('fetch', uid, '(RFC822)')
                # if uid == b'5384':
                #     print(data[0][1])
                matches = re.findall(b'charset=(.+?);', data[0][1])
                if len(matches) == 0:
                    matches = re.findall(b'charset="*(.+?)["\s]', data[0][1])
                encoding = matches[0].decode('utf-8','ignore')
                raw_email = data[0][1].decode(encoding)
                email_message = email.message_from_string(raw_email)
                email_date = email_message['Date']
                email_date = datetime.strptime(email_date[:31], '%a, %d %b %Y %H:%M:%S %z')
                result = {}
                if email_date < target_end_date:
                    result['message'] = email_message
                    result['uid'] = uid
                    result['sent'] = email_date
                    result['text'] = self._get_first_text_block(email_message)
                    results.append(result)

                count += 1
            print('folder', folder, 'size', count)
        return results

    def _find_agent_reference(self, text):
        message_text = remove_html_tags(text)
        clean_message = previous_line = ''
        for lin in message_text.split('\n'):
            line = lin.strip()
            line = re.sub(r'^> *.*?$', '', line)
            if len(line) > 0:
                line = previous_line + line
                _original = len(re.findall(r'----.*(Original|Forwarded) message.*-{4,10}', line, re.I))
                _wrote = len(re.findall(r'^On.+?wrote:$', line, re.I))
                if _original or _wrote:
                    break
                clean_message += line + '\n'
                previous_line = line

        # normalize & collect names
        names = []
        for name in NIKNAMES:
            for nick in NIKNAMES[name]:
                clean_message = clean_message.replace(nick, name)
                if clean_message.count(name):
                    names.append(name)

        sign_matches = re.findall(r'^--(.*?)IT Support Analyst', clean_message, re.DOTALL|re.MULTILINE)
        # print('sings', len(sign_matches))
        signatures = []
        match = False
        if len(sign_matches) > 0:
            #find proper
            for sign in sign_matches:
                for name in NIKNAMES:
                    if sign.count(name):
                        signatures.append(name)
                        
            #find erroneous
            if not len(signatures):
                # print('\tSIGNATURE DETECTED< BUT NO MATCH OF NAME WITHIN IT', sign_matches)
                clean_lines = clean_message.split('\n')
                for i in range(len(clean_lines)):
                    for name in NIKNAMES:
                        if clean_lines[i].count(name)>0:
                            next2lines = ''.join(clean_lines[i:i+2])
                            erroneous_signatures = re.findall(name + r'\s*?--.*?IT Support Analyst', next2lines)
                            if len(erroneous_signatures):
                                print('\tERRONEOUS_SIGNATURE by', name)
                                signatures.append(name)
        
        if len(signatures):
            results = signatures
        elif len(names):
            results = names
        else:
            return None
        # print(uid, email_date, '~ RESULT:', result)
        return results

    # def _old_determine_agents(self, messages):
    #     for message in messages:
    #         # print('-'*20)
    #         safe_print(message['uid'])
    #         # print('-'*20)
    #         # print('~'*60, uid, email_date, '~'*60)
    #         # safe_print(text)
    #         potential_names = self._find_agent_reference(message['text'])
    #         potential_shifts = Shift.objects.filter(date__range=(message['sent'] - timedelta(hours=8),message['sent']))
    #         if not len(potential_shifts):
    #             potential_shifts = Shift.objects.filter(date__range=(message['sent'].replace(hour=0, minute=0, second=0), message['sent'].replace(hour=23,minute=59,second=59)))
    #         if not len(potential_shifts):
    #             raise MyError('No matching shifts for email %s sent on %s' % (message['uid'], message['sent'].strftime("%Y-%m-%d %H:%M")))

    #         matches = []
    #         if potential_names:
    #             for shift in potential_shifts:
    #                 for name in potential_names:
    #                     if shift.agent.name == name:
    #                         matches.append(shift)

    #         if len(matches) == 0:
    #             #trust the shift
    #             if len(potential_shifts) == 1:
    #                 message['shift'] = potential_shifts[0]
    #             else:
    #                 if message['sent'] < message['sent'].replace(hour=12, minute=0, second=0):
    #                     message['shift'] = potential_shifts.order_by('date')[0]
    #                 else:
    #                     message['shift'] = potential_shifts.order_by('-date')[0]
    #         elif len(matches) == 1:
    #             message['shift'] = matches[0]
    #         else:
    #             #message sent during overlap, and both agent names apear in the email text
    #             matches.sort(key=lambda x: x.date)
    #             # print('sorted matches', matches)
    #             if message['sent'] < message['sent'].replace(hour=12, minute=0, second=0):
    #                 message['shift'] = matches[0]
    #             else:
    #                 message['shift'] = matches[-1]

    #         message['agent'] = message['shift'].agent

    #     return messages

    def _determine_agents(self, messages):
        for message in messages:
            safe_print(message['uid'])
            # safe_print(text)
            potential_names = self._find_agent_reference(message['text'])
            potential_shifts = Shift.objects.filter(date__range=(message['sent'] - timedelta(hours=8),message['sent']))
            if not len(potential_shifts):
                potential_shifts = Shift.objects.filter(date__range=(message['sent'].replace(hour=0, minute=0, second=0), message['sent'].replace(hour=23,minute=59,second=59)))
            if not len(potential_shifts):
                raise MyError('No matching shifts for email %s sent on %s' % (message['uid'], message['sent'].strftime("%Y-%m-%d %H:%M")))

            matches = []
            if potential_names:
                for shift in potential_shifts:
                    for name in potential_names:
                        if shift.agent.name == name:
                            matches.append(shift)

            if len(matches) == 0:
                # drop the missing
                message['shift'] = message['agent'] = None
            elif len(matches) == 1:
                message['shift'] = matches[0]
                message['agent'] = message['shift'].agent
            else:
                # message sent during overlap, and both agent names apear in the email text
                matches.sort(key=lambda x: x.date)
                if message['sent'] < message['sent'].replace(hour=12, minute=0, second=0):
                    message['shift'] = matches[0]
                else:
                    message['shift'] = matches[-1]
                message['agent'] = message['shift'].agent

        return messages

    def pickleit(self, data):
        pickle.dump(data, open(PICKLE_PATHFILE + self.account + ".pickle", "wb" ))

    def depickleit(self):
        return pickle.load(open(PICKLE_PATHFILE + self.account + ".pickle", "rb"))

    def temporary_view_for_kpi_use(self, target_box, target_start_date, target_end_date=timezone.now(), source='web'):
        self.account = target_box
        if source == 'web':
            box = self._open_box(settings.BOX_SPECS[target_box]['user'], settings.BOX_SPECS[target_box]['pass'], settings.BOX_SPECS[target_box]['host'], settings.BOX_SPECS[target_box]['port'])
            messages = self._pull_messages(box, target_start_date, target_end_date)
            self._close_box(box)
            if self.account == 'WLK':
                self.pickleit(messages)
            print('---------------------------------------> pickled')
        else:
            messages = self.depickleit()
        messages = self._determine_agents(messages)
        return messages

