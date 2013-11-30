import imaplib, email, re, sys, pickle
from email.parser import Parser
from datetime import datetime, timedelta, date
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Case, SupportEmail
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

PICKLE_PATHFILE = settings.LOCATION_PATHS['pickle_folder']

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

# uid = models.CharField(max_length=12, unique=True)
# date = models.DateTimeField() # unique=True ??
# subject = models.CharField(max_length=1024)
# sender = models.EmailField()
# recipient = models.EmailField()
# message = models.TextField()
# sfdc = models.CharField(max_length=3, choices=SFDC_ACCOUNTS, default=None, null=True)
# agent = models.ForeignKey(Agent, null=True)
# shift = models.ForeignKey(Shift)
# case = models.ForeignKey(Case, blank=True, null=True)

MODEL_FIELDS = ['uid', 'date', 'subject', 'sender', 'recipient', 'message', 'sfdc', 'agent', 'shift', 'case', 'contact']

class EmailCollector:
    def __init__(self, debug=None):
        self.debug = debug
        self.account = None

    def _open_box(self, user, password, host, port):
        box = imaplib.IMAP4_SSL(host=host, port=port)
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
                if self.account == 'WLK' and uid in [b'525', b'529', b'966', b'967', b'1020']: # not sure what happens, but connection seems to hang. It occurs only on stupid MS servers
                    print('skipping', uid)
                else:
                    print('uid::', uid)
                    result, data = box.uid('fetch', uid, '(RFC822)')
                    # if uid == b'5384':
                    #     print(data[0][1])
                    matches = re.findall(b'charset=(.+?);', data[0][1])
                    print('\t\tmatches1', matches)
                    if len(matches) == 0:
                        matches = re.findall(b'charset="*(.+?)["\s]', data[0][1])
                        print('\t\tmatches2', matches)
                    if len(matches) > 0:
                        encoding = matches[0].decode('utf-8','ignore')
                        try:
                            print('\t\ttrying decode with encoding', encoding)
                            raw_email = data[0][1].decode(encoding)
                        except LookupError as e:
                            print(e)
                            raw_email = data[0][1].decode('utf-8','ignore')
                    else:
                        print('no encoding found for message', uid)
                        raw_email = data[0][1].decode('utf-8','ignore')
                    print('\tmessage is decoded')
                    email_message = email.message_from_string(raw_email)
                    print('\tmessage is parsed from string')
                    email_date = email_message['Date']
                    email_date = datetime.strptime(email_date[:31], '%a, %d %b %Y %H:%M:%S %z')
                    for k in email_message.keys():
                        print(k, ':', email_message[k])
                        print('-='*10)
                    print()
                    result = {}
                    if email_date < target_end_date:
                        result['uid'] = uid.decode('ascii')
                        result['sfdc'] = self.account
                        result['date'] = email_date
                        result['subject'] = email_message['subject']
                        result['sender'] = email_message['from']
                        result['recipient'] = email_message['to']#.replace('<', '&lt;').replace('>', '&gt;')
                        result['message'] = self._get_first_text_block(email_message)
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

    def _determine_agents(self, messages):
        for message in messages:
            safe_print(message['uid'])
            # safe_print(text)
            potential_names = self._find_agent_reference(message['message'])
            potential_shifts = Shift.objects.filter(date__range=(message['date'] - timedelta(hours=8),message['date']))
            if not len(potential_shifts):
                potential_shifts = Shift.objects.filter(date__range=(message['date'].replace(hour=0, minute=0, second=0), message['date'].replace(hour=23,minute=59,second=59)))
            if not len(potential_shifts):
                raise MyError('No matching shifts for email %s sent on %s' % (message['uid'], message['date'].strftime("%Y-%m-%d %H:%M")))

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
                if message['date'] < message['date'].replace(hour=12, minute=0, second=0):
                    message['shift'] = matches[0]
                else:
                    message['shift'] = matches[-1]
                message['agent'] = message['shift'].agent

        return messages

    def _determine_contacts(self, messages):
        #not implemented
        for message in messages:
            message['contact'] = None
        return messages

    def pickleit(self, data):
        pickle.dump(data, open(PICKLE_PATHFILE + self.account + ".pickle", "wb" ))

    def depickleit(self):
        return pickle.load(open(PICKLE_PATHFILE + self.account + ".pickle", "rb"))

    def save(self, messages):
        for message in messages:
            mail = SupportEmail.objects.filter(uid = message['uid'])
            if mail:
                mail = mail[0]
                for k in MODEL_FIELDS:
                    if k in message.keys():
                        setattr(mail, k, message[k])
            else:
                mail = SupportEmail(**message)
            mail.save()

    def temporary_view_for_kpi_use(self, target_box, target_start_date, target_end_date=timezone.now()):
        self.account = target_box
        # pull all messages by period
    
        box = self._open_box(settings.BOX_SPECS[target_box]['user'], settings.BOX_SPECS[target_box]['pass'], settings.BOX_SPECS[target_box]['host'], settings.BOX_SPECS[target_box]['port'])
        messages = self._pull_messages(box, target_start_date, target_end_date)
        self._close_box(box)
        # filter out service emails - chase, forms & etc
        internal = lambda address: address.count('@reflective.com') or address.count('@reflectivebg.com') or address.count('itsupport@wightlink.co.uk')
        messages = [ z for z in messages if not internal(z['recipient']) ]
        # find foreign keys
        messages = self._determine_agents(messages)
        messages = self._determine_contacts(messages)
        # store in the DB
        self.save(messages)
        print(len(messages), 'emails saved in the DB for the period ', target_start_date, '-', target_end_date)

        return messages

