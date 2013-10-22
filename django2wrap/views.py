import imp
import time, os
from datetime import datetime, timedelta
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
    # update - pull specific subset of a resourse, add the new ones, and update old records in db
    #   update would need more form fields (agent, time period[hour,day,week, month], )
    # view   - show records from db - may use same subset fields as in "update"
    # reload - empty db, pull all records from resourse, and save them to db
    # load   - (basic) pull all records from resourse
    # wipe   - (basic) empty db
    # save   - (basic) save the data to db, overwrite existing records
    # sync   - (basic) save the data to db, skip existing records

    # until I can pass via south the model changes for "Resource", I should use a dict:
    actions = ['Update', 'View', 'Reload'] #make this Meta -- passing to form and to coresponding method getattr(foo, 'bar')()


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

def chase(request):
    last_time = Resource.objects.get(name='cases').last_sync
    if request.method == "POST":
        # update_debug = CaseCollector.update(target_view = 'open')
        update_debug = actuator_classes['cases']().update(target_view = 'open')
        header = ['number', 'status', 'subject', 'postpone', 'target_chase', 'last_comment',]
        all_open_cases = Case.objects.exclude(status__contains = 'Close')
        querysets = {
            'WLK': {
                'init'     : {'base': None,       'attr': 'exclude', 'params': {'status__contains': 'Close'}, 'results': all_open_cases}, 
                'total'    : {'base': 'init',     'attr': 'filter',  'params': {'sfdc': 'WLK'},    'results': None}, 
                'to_chase' : {'base': 'total',    'attr': 'filter',  'params': {'chased': False},  'results': None},
                'postponed': {'base': 'to_chase', 'attr': 'exclude', 'params': {'postpone': None}, 'results': None},
            },
            'RSL': {
                'init'     : {'base': None,       'attr': 'exclude', 'params': {'status__contains': 'Close'}, 'results': all_open_cases}, 
                'total'    : {'base': 'init',     'attr': 'filter',  'params': {'sfdc': 'RSL'},    'results': None}, 
                'to_chase' : {'base': 'total',    'attr': 'filter',  'params': {'chased': False},  'results': None},
                'postponed': {'base': 'to_chase', 'attr': 'exclude', 'params': {'postpone': None}, 'results': None},
            },
        }

        
        data = [['Parameter', 'WIGHTLINK', 'REFLECTIVE'],]
        for key in list(querysets['WLK'].keys())[1:]:
            data.append(['Count of %s Cases' % key.capitalize()])
            for sfdc in ['WLK', 'RSL']:
                obj_key_ref = querysets[sfdc][key]['base']
                print(key,sfdc,obj_key_ref)
                objects = querysets[sfdc][obj_key_ref]['results']
                objects = getattr(objects, querysets[sfdc][key]['attr'])(**querysets[sfdc][key]['params'])
                querysets[sfdc][key]['results'] = objects[:]
                data[-1].append(len(objects))
            if key == 'to_chase':
                data[-1] = [ (z, '#FF0000') for z in data[-1] ]

        # tables = {'Wightlink to Chase': [header,], 'Wightlink Postponed': [header,],'Reflective to Chase': [header,],'Reflective Postponed': [header,]}
        tables = {'WLK to_chase': [header,], 'WLK postponed': [header,],'RSL to_chase': [header,],'RSL postponed': [header,]}
        keys = ['WLK to_chase', 'RSL to_chase', 'WLK postponed', 'RSL postponed'] # to preserve order
        for key in keys:
            qs = querysets[key.split(' ')[0]][key.split(' ')[1]]['results']
            print(key, qs)
            for case in qs:
                row = [ getattr(case, z) for z in header ]
                row[-1] = row[-1]()
                print('\t',key, row)
                tables[key].append(row)
        
        # print(tables)


        # data = [
        #     ['Parameter', 'WIGHTLINK', 'REFLECTIVE'],
        #     ['States considered as pending to support:', ['New', 'In Progress', 'Responded'], ['New', 'Responded', 'Working on Resolution']],
        #     ['Open Cases Total Count:', querysets['WLK']['total'], Case.objects.filter(sfdc='RSL').exclude(status__contains='Close')],
        #     ['Cases to Chase Count:', Case.objects.filter(sfdc='WLK', chased=False).exclude(status__contains='Close'), Case.objects.filter(sfdc='RSL', chased=False).exclude(status__contains='Close')],
        #     [ (z, '#FF0000') for z in ['Cases to Chase Count:', Case.objects.filter(sfdc='WLK', chased=False).exclude(status__contains='Close'), Case.objects.filter(sfdc='RSL', chased=False).exclude(status__contains='Close')] ],
        #     ['Cases with "Postponed Chase" Count:', Case.objects.filter(sfdc='WLK').exclude(status__contains='Close', postpone=None), Case.objects.filter(sfdc='RSL').exclude(status__contains='Close', postpone=None)],
        # ]
        message = data



        result = TemplateResponse(request, 'chase.html', locals())
        # with open(chaser.LAST_REUSLTS,'w', encoding='utf-8') as fff:
        #     fff.write(result.rendered_content)
    else:
        result = render(request, 'chase.html', locals())

    return result


def chased(request):
    pass