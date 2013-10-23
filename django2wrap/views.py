import imp, os
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from email.mime.multipart import MIMEBase
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.mail import send_mail, mail_admins, mail_managers, EmailMessage, EmailMultiAlternatives
from django2wrap.forms import EscalationForm, LicenseForm, SyncDetailsForm
# from django.db.models import Max
from django2wrap.models import Agent, Shift, Case, Call, Comment, Resource
from django.template.response import TemplateResponse
# from django2wrap.cases import CaseCollector 
# from . import chase as chaser

#load resources
resources = Resource.objects.all()
actuator_classes = {}
for res in resources:
    actuator_classes[res.name] = getattr(imp.load_source(res.class_name, res.module), res.class_name)

# PhoneCalls = getattr(imp.load_source('PhoneCalls', 'django2wrap/calls.py'), 'PhoneCalls')

# PhoneCalls = imp.load_source('PhoneCalls', 'django2wrap/calls.py').getattr(actuator, action.lower())(clean_data['agent'], clean_data['from_date'])
# ScheduleShifts = imp.load_source('ScheduleShifts', 'django2wrap/shifts.py')
# from django2wrap.calls import PhoneCalls # as phonecalls
# from django2wrap.shifts import ScheduleShifts 
# actuator_classes = {'calls': PhoneCalls, 'shifts': ScheduleShifts }

def homepage(request):
    return HttpResponse('<html><body>Welcome<br><br><a href="/chase/">Chaser</a><br><a href="https://78.142.1.136/mwiki/">Wiki</a><br><a href="/escalation/">Escalation Form</a><br><a href="/license/">License Form</a></body></html>')

def escalation_form(request):
    if request.method == 'POST':
        form = EscalationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            subject = "escalation case: " + cd['case'] + " priority: " + cd['priority']
            message = settings.ESCALATION_MESSAGE_BODY
            for key in ['agent', 'case', 'priority', 'company', 'contact', 'description', 'investigated']:
                message = message.replace('*' + key + '*', cd[key])
            if cd['case'] == "0000":
                to = ['Iliyan <iliyan@reflectivebg.com>'] #, peter@reflectivebg.com']
            else:
                to = settings.ESCALATION_CONTACTS
            mymail = EmailMultiAlternatives(subject, message, 'Support <support@reflective.com>', to, headers = {'Reply-To': 'support@reflective.com'})
            mymail.attach_alternative(message, 'text/html')
            mymail.send(fail_silently=False)
            return HttpResponseRedirect('/')
    else:
        form = EscalationForm()
    return render(request, 'escalation_form.html', {'form': form})

def license_form(request):
    if request.method == 'POST':
        form = LicenseForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            subject = "license request case: " + cd['case'] + " priority: " + cd['priority']
            message = settings.LICENSE_MESSAGE_BODY
            for key in ['agent', 'case', 'priority', 'requestor', 'company', 'contact', 'hostid', 'product', 'license_type', 'license_status', 'license_function',]:
                message = message.replace(key, cd[key])
            for key in ['pather_company', 'period', 'notes',]:
                message = message.replace(key, "<tr><td><label>"+key.capitalize()+"</label></td><td>%s</td></tr>" % cd[key])
            message = message.replace("Pather_company", "Client")
            if cd['case'] == "0000":
                to = ['Iliyan <iliyan@reflectivebg.com>'] #, peter@reflectivebg.com']
            else:
                to = settings.LICENSE_CONTACTS

            mymail = EmailMultiAlternatives(subject, message, 'Support <support@reflective.com>', to, headers = {'Reply-To': 'support@reflective.com'})
            mymail.attach_alternative(message, 'text/html')
            if request.FILES:
                hostid_form = request.FILES['host_id_change_form']
                try:
                    mymail.attach(hostid_form.name, hostid_form.read(), hostid_form.content_type)
                except:
                    return "Attachment error"

            mymail.send(fail_silently=False)
            return HttpResponseRedirect('/')
    else:
        form = LicenseForm()
    return render(request, 'license_form.html', {'form': form})

def listen(request, agent = 'Boris', file_name = '+000000_2012.06.15.Fri.17.40.37.mp3', callid = None):
    # note that MP3_STORAGE should not be in MEDIA_ROOT
    if callid:
        the_call = Call.objects.get(id=callid)
        fname = os.path.join(settings.MP3_STORAGE, the_call.agent.name, the_call.filename)
    else:
        fname = os.path.join(settings.MP3_STORAGE, agent, file_name)
    with open (fname, "rb") as f:
        data = f.read()
    response = HttpResponse()
    response.write(data)
    response['Content-Type'] = 'audio/mp3'
    response['Content-Length'] = os.path.getsize(fname)
    return response

def sync(request):
    actions = ['Update', 'View', 'Reload']
    if request.method == 'POST':
        form = SyncDetailsForm(request.POST)
        if form.is_valid():
            clean_data = form.cleaned_data
            if clean_data['agent'] == 'None':
                clean_data['agent'] = None
            if clean_data['from_date']:
                # clear the time -- just for the time being
                clean_data['from_date'] = datetime(*tuple( getattr(clean_data['from_date'], z) for z in ['year', 'month', 'day'] ))
            action = request.POST['action'] #form can render select box, and I'm going for a several submit buttons
            actuator = actuator_classes[clean_data['system']]()
            results = getattr(actuator, action.lower())(clean_data['agent'], clean_data['from_date'])
    else:
        form = SyncDetailsForm()
    return render(request, 'sync.html', locals())

def chase(request, run_update_before_chase = False):
    last_time = Resource.objects.get(name='cases').last_sync
    if request.method == "POST" or not run_update_before_chase:
        if run_update_before_chase:
            # update_debug = actuator_classes['cases']().update(target_time = timezone.now() + timedelta(days=-1))
            update_results = actuator_classes['cases']().update(target_view = 'open')
        else:
            update_results = None
        header = ['number', 'status', 'subject', 'postpone', 'target_chase', 'last_comment', 'link']
        all_open_cases = Case.objects.exclude(status__contains = 'Close')
        querysets = {
            'WLK': {
                'init'     : {'base': None,    'attr': 'exclude', 'params': {'status__contains': 'Close'}, 'results': all_open_cases}, 
                'total'    : {'base': 'init',  'attr': 'filter',  'params': {'sfdc': 'WLK'},    'results': None}, 
                'to_chase' : {'base': 'total', 'attr': 'filter',  'params': {'chased': False},  'results': None},
                'postponed': {'base': 'total', 'attr': 'exclude', 'params': {'postpone': None}, 'results': None},
            },
            'RSL': {
                'init'     : {'base': None,    'attr': 'exclude', 'params': {'status__contains': 'Close'}, 'results': all_open_cases}, 
                'total'    : {'base': 'init',  'attr': 'filter',  'params': {'sfdc': 'RSL'},    'results': None}, 
                'to_chase' : {'base': 'total', 'attr': 'filter',  'params': {'chased': False},  'results': None},
                'postponed': {'base': 'total', 'attr': 'exclude', 'params': {'postpone': None}, 'results': None},
            },
        }
        data = [['Parameter', 'WIGHTLINK', 'REFLECTIVE'],]
        for key in list(querysets['WLK'].keys())[1:]:
            data.append(['Count of %s Cases' % key.capitalize()])
            for sfdc in ['WLK', 'RSL']:
                obj_key_ref = querysets[sfdc][key]['base']
                # print(key,sfdc,obj_key_ref)
                objects = querysets[sfdc][obj_key_ref]['results']
                objects = getattr(objects, querysets[sfdc][key]['attr'])(**querysets[sfdc][key]['params'])
                querysets[sfdc][key]['results'] = objects[:]
                data[-1].append(len(objects))
            if key == 'to_chase':
                data[-1] = [ (z, 'style="background-color:#FF0000;"') for z in data[-1] ]
        URLS = {
            'WLK': '<a href="https://eu1.salesforce.com/%s" target="_blank">%s</a>',
            'RSL': '<a href="https://emea.salesforce.com/%s" target="_blank">%s</a>',
        }
        table = []
        cases_closed_since_last_chase = []
        keys = ['WLK to_chase', 'RSL to_chase', 'WLK postponed', 'RSL postponed'] # to preserve order
        for key in keys:
            if key.count('to_chase'):
                color = '#FF0000'
            else:
                color = '#AAAAAA'
            table.append([('<h2>' + key + '</h2>', 'style="background-color:' + color + ';text-align:center;" colspan="' + str(len(header)) + '"')])
            table.append([ ('<b>' + z + '</b>', 'style="text-align:center;"') for z in header[:-1] ])
            qs = querysets[key.split(' ')[0]][key.split(' ')[1]]['results']
            for case in qs:
                row = [ getattr(case, z) for z in header ]
                link = row.pop()
                row[0] = URLS[key.split(' ')[0]] % (link, row[0])
                row[-1] = row[-1]()
                if update_results and case.number not in [ z['number'] for z in update_results ]:
                    cases_closed_since_last_chase.append(row)
                else:
                    # tables[key].append(row)
                    table.append(row)

        result = render(request, 'chase.html', {'last_time': last_time, 'data': data, 'table': table, 'cases_closed_since_last_chase': cases_closed_since_last_chase})
        email_result = render(request, 'chase.html', {'data': data, 'table': table})
        raw_result = email_result.content.decode('utf-8')
        if "sendit" in request.POST.keys():
            mymail = EmailMultiAlternatives("Daily Chase Status " + datetime.now().strftime("%H:%M"), str(data)+'\n'+str(table), settings.CHASE_EMAIL_FROM, settings.CHASE_EMAIL_TO, headers = settings.CHASE_EMAIL_HEADERS)
            mymail.attach_alternative(raw_result, 'text/html')
            mymail.send(fail_silently=False)
    else:
        result = render(request, 'chase.html', {'last_time': last_time})

    return result

# def mailit(message):
#     import smtplib
#     from email.mime.multipart import MIMEMultipart
#     from email.mime.text import MIMEText
#     from time import localtime, strftime
#     subject  = "Daily Chase Status " + strftime("%H:%M", localtime())

#     # inclusion ---------------------------------------------
#     msg = MIMEMultipart('alternative')
#     msg['Subject'] = subject
#     msg['From'] = FROMADDR
#     msg['To'] = ','.join(TOADDRS)

#     # Create the body of the message (a plain-text and an HTML version).
#     # text = "this message is not available in plain text"
#     # part1 = MIMEText(text, 'plain')
#     part2 = MIMEText(message, 'html', 'utf-8')
#     # msg.attach(part1)
#     msg.attach(part2)
#     # end of inclusion --------------------------------------

#     server = smtplib.SMTP('smtp.gmail.com', 587)
#     server.set_debuglevel(0)
#     server.ehlo()
#     server.starttls()
#     server.login(LOGIN, PASSWORD)
#     server.sendmail(FROMADDR, TOADDRS, msg.as_string())
#     server.quit()