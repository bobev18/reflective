import imaplib, email, re, sys
from datetime import datetime, timedelta, date
from django.conf.settings import EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

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

def get_first_text_block(email_message_instance):
    for part in email_message_instance.walk():
        if part.get_content_maintype() == 'text':
            return part.get_payload()
    
mail = imaplib.IMAP4_SSL(host=EMAIL_HOST, port=993)
mail.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
# print('mail folders', mail.list())
mail.select(mailbox='"[Gmail]/Sent Mail"', readonly=False)
since_date = date(2013,9,1).strftime("%d-%b-%Y")
result, data = mail.uid('search', None, '(SENTSINCE {date})'.format(date=since_date))
all_messages = data[0].split()
print('all_messages', len(all_messages))
for uid in all_messages:
    # print('uid::', uid)
    result, data = mail.uid('fetch', uid, '(RFC822)')
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
    # if email_date < email_date.replace(month=10, day=1, hour=0):
    if 1:
        # print('~'*60, uid, email_date, '~'*60)
        message_text = get_first_text_block(email_message)
        # safe_print(message_text)

        message_text = remove_html_tags(message_text)

        lines = message_text.split('\n')
        clean_message = ''
        last_line = ''
        drop_the_rest = False
        for line in lines:
            l = line.strip()
            l = re.sub(r'^> *.*?$', '', l)
            # print('dashes:', re.findall(r'^----',l))
            # print('words :', re.findall(r'(Original|Forwarded) message',l))
            # print('modash:', re.findall(r'[^-]-{4,10}',l))
            _original = len(re.findall(r'----.*(Original|Forwarded) message.*-{4,10}', l, re.I))
            _wrote = len(re.findall(r'^On.+?wrote:$', l, re.I))
            if not _wrote and len(re.findall(r'wrote:$', l)):
                l = last_line + l
                _wrote = len(re.findall(r'^On.+?wrote:$', l, re.I))
            # if l.count('-----Original Message-----'):
            #     print('>'*10, l, '<'*10)
            if _original or _wrote:
                # print('ORIGINAL*'*15)
                drop_the_rest = True

            for name in NIKNAMES:
                for nick in NIKNAMES[name]:
                    l = l.replace(nick, name)

            if len(l) > 0 and not drop_the_rest:
                clean_message += l + '\n'
                last_line = l

        # safe_print(clean_message)

        # --[^I]+?IT Support Analyst
        signatures = re.findall(r'^--(.*?)IT Support Analyst', clean_message, re.DOTALL|re.MULTILINE)
        # signatures = re.findall(r'^-- *$(.*?)IT Support Analyst', message_text, re.DOTALL|re.MULTILINE)
        match = False
        result = None
        if len(signatures) > 0:
            # print('sings', len(signatures))
            signs = []
            match = False
            for sign in signatures:
                for name in NIKNAMES:
                    if sign.count(name):
                        signs.append(name)
                        match = True
            if not match:
                # print('\tSIGNATURE DETECTED< BUT NO MATCH OF NAME WITHIN IT', signatures)
                clean_lines = clean_message.split('\n')
                for i in range(len(clean_lines)):
                    for name in NIKNAMES:
                        if clean_lines[i].count(name)>0:
                            nextlines = ''.join(clean_lines[i:])
                            erroneous_signatures = re.findall(name + r'\s*?--(.*?)IT Support Analyst', nextlines)
                            if len(erroneous_signatures):
                                print('\tERRONEOUS_SIGNATURE by', name)
                                signs.append(name)
            if len(signs) > 0:
                result = signs


        if not match:
            names = []
            for name in NIKNAMES:
                if clean_message.count(name):
                    names.append(name)
                    match = True

            if match:
                if len(names) == 1:
                    pass
                    # print('NAME MATCH :', names[0])
                else:
                    pass
                    # print('FOUND NAMES:', ', '.join(names))
                result = names




        # if not match:
        #     safe_print(clean_message)

        print(uid, email_date, '~ RESULT:', result)


print('done')

mail.close()
mail.logout()