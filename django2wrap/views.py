import imp, os
from calendar import monthrange
from datetime import datetime, timedelta, date
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
from django2wrap.weekly_report import WeeklyReport
from django2wrap.cases import CaseCollector, MODEL_ARG_LIST, SUPPORT_STATUSES, SLA_RESPONSE
case_collector = CaseCollector()
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

def strdate(dt):
    tz = timezone.get_current_timezone()
    if type(dt) == datetime:
        return timezone.make_naive(dt, tz).strftime("%d/%m/%Y %H:%M")
    elif type(dt) == date:
        return timezone.make_naive(dt, tz).strftime("%d/%m/%Y")
    else:
        return dt

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
        cases_closed_since_last_chase = []
        all_open_cases = Case.objects.exclude(status__contains = 'Close') #db
        open_numbers = [ (getattr(z, 'number'), getattr(z, 'sfdc')) for z in all_open_cases ]
        update_results = None
        if run_update_before_chase:
            update_results = case_collector.update(target_view = 'open') #web
            for num_sfdc in open_numbers: #db
                if num_sfdc not in [ (z['number'], z['sfdc']) for z in update_results ]: #db not in web
                    all_open_cases = all_open_cases.exclude(number = num_sfdc[0], sfdc = num_sfdc[1]) #db adjusted
                    cases_closed_since_last_chase.append(num_sfdc)

        header = ['number', 'status', 'subject', 'postpone', 'target_chase', 'last_comment', 'link']
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
                row = [ strdate(z) for z in row ]
                if update_results and case.number not in [ z['number'] for z in update_results ]:
                    pass
                    # cases_closed_since_last_chase.append(row)
                else:
                    # tables[key].append(row)
                    table.append(row)

        for num, sfdc in cases_closed_since_last_chase:
            case_collector.update_one(target = num, sfdc = sfdc)

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

def weekly(request, run_update_before_chase = True):
    # last_time = Resource.objects.get(name='cases').last_sync
    if run_update_before_chase:
        update_results = case_collector.update(target_time = timezone.now() - timedelta(days=8))
    else:
        update_results = None

    report = WeeklyReport()
    data = report.action()

    result = render(request, 'results.html', {'title': 'Weekly Report', 'data': data})
    return result

def update_case(request, link = None, number = None, sfdc = None):
    if link:
        cases = Case.objects.get(link=link)
    if number:
        if len(number) < 8:
            number = number.rjust(8,'0')
        cases = Case.objects.filter(number=number)

    if len(cases) == 1:
        case = cases[0]
    elif len(cases) > 1:
        if not sfdc:
            links = ''
            for case in cases:
                links += '<a href="' + request.path + case.sfdc + '">' + case.sfdc + '</a><br>'
            return HttpResponse('<html><body>Select SFDC<br><br>' + links + '</body></html>')
        else:
            case = cases.get(sfdc = sfdc)
    else:
        # return HttpResponse('<html><body>No matching cases with number</body></html>')
        case = None

    data = [['name', 'old', 'new']]
    # MODEL_ARG_LIST = ['number', 'status', 'subject', 'description', 'sfdc', 'created', 'closed', 'system', 'priority', 'reason', 'contact', 'link', 'shift', 'creator', 'in_support_sla', 'in_response_sla', 'support_sla', 'response_sla', 'support_time', 'response_time', 'raw', 'postpone', 'target_chase', 'chased' ]

    if case:
        for item in MODEL_ARG_LIST:
            data.append([item, getattr(case, item)])
        update_results = case_collector.update_one(target = case)
    else:
        for item in MODEL_ARG_LIST:
            data.append([item, 'n/a'])
        results = case_collector.update(target_time = timezone.now().replace(hour = 0, minute = 0, second = 0, microsecond = 0), target_view = 'all') # returns list of dicts
        update_results = [ z for z in results if z['number'] == number]
        if len(update_results) > 0:
            update_results = update_results[0]
        else:
            return HttpResponse('<html><body>No matching cases with number %s</body></html>' % number)

        # return HttpResponseRedirect('/')
    for i in range(1,len(MODEL_ARG_LIST) + 1):
        data[i].append(update_results[MODEL_ARG_LIST[i-1]])
        if isinstance(data[i][-1],tuple): # clears tuoples of contact links, which get interpreting as style for the field
            data[i][-1] = str(data[i][-1])
        if data[i][-1] != data[i][-2]: # add style if field has changed
            data[i][-1] = (data[i][-1], 'style="background-color:#FF0000;"')

    return render(request, 'results.html', {'title': 'Case Update', 'data': data})

def kpi(request, run_update_before_chase = False):
    if run_update_before_chase:
        update_results = case_collector.update(target_time = timezone.now() - timedelta(days=31))
    else:
        update_results = None

    report = WeeklyReport()
    data = report.action()

    result = render(request, 'results.html', {'title': 'Weekly Report', 'data': data})
    return result

def monthly(request, sfdc, target_month = None, run_update_before_chase = False):

    def calculate_monthly(records):
        for k in range(len(records)):
            syslabox[records[k].system]['count']        += 1
            syslabox[records[k].system]['out_sup_sla']  += not records[k].in_support_sla
            syslabox[records[k].system]['out_resp_sla'] += not records[k].in_response_sla
            syslabox[records[k].system]['combined']     += not (records[k].in_response_sla and records[k].in_support_sla)
        for sla_type in ['out_sup_sla', 'out_resp_sla', 'combined']:
            syslabox['total'][sla_type] = sum([ syslabox[z][sla_type] for z in SYSTEMS[sfdc] ])

    if not target_month or not isinstance(target_month, datetime):
        target_month = datetime(timezone.now().year, timezone.now().month - 1, 1, 0, 0, 0)
    elif isinstance(target_month, str):
        target_month_str = target_month
        target_month = datetime.strptime('1' + target_month, '%d/%m/%Y')
    else:
        return HttpResponseRedirect('/')
    if run_update_before_chase:
        update_results = case_collector.update(target_time = target_month, target_sfdc = sfdc)
    else:
        update_results = None

    OUT_SLA_VIEW_DETAILS = {
        'WLK': ['system', 'priority'],
        'RSL' : ['reason', 'problem']
    }
    SYSTEMS = {
        'WLK': ['Ferry+', 'CDI', 'Email', 'Local PC', 'Sentinel', 'DRS', 'Intranet', 'Document Management', 'Blackberry Server', 'CRM', 'Profit Optimisation (RTS)', 'Wide Area Network', 'Great Plains', 'RPO', 'Sailing Statistics (AIS)', 'NiceLabel'],
        'RSL' : ['StressTester', 'Sentinel', 'Load Monitor']
    }

    syslabox = {
        'total': {'count': 0, 'out_sup_sla': 0, 'out_resp_sla':0, 'combined':0},
        'WLK'  : {'count': 0, 'out_sup_sla': 0, 'out_resp_sla':0, 'combined':0},
        'RSL'  : {'count': 0, 'out_sup_sla': 0, 'out_resp_sla':0, 'combined':0},
    }
    for sys in SYSTEMS[sfdc]:
        syslabox[sys] = {'count': 0, 'out_sup_sla': 0, 'out_resp_sla':0, 'combined':0}
    fields = ['in_support_sla', 'number', 'subject', 'in_response_sla', 'number', 'subject', 'response_time', 'number', 'subject', 'support_sla', 'support_time', 'system', 'priority']
    target_month_str = target_month.strftime('/%m/%Y')
    end_of_month = target_month + timedelta(days = monthrange(target_month.year, target_month.month)[1])
    records = Case.objects.filter(closed__range = (target_month, end_of_month), sfdc = sfdc)
    records = sorted(records, key = lambda x: x.number)
    calculate_monthly(records) #generates the stats
    mo_len = len(records)
    results = ''
    results += "SFDC account: " + sfdc + '\n'
    results += 'Target: all cases closed in:' + target_month_str + '\n'
    results += 'Records count:' + str(mo_len) + '\n'
    results += '-------------------------------' + '\n'
    results += "States considered as pending to support: " + str(SUPPORT_STATUSES[sfdc]) + '\n'
    for rec in records:
        card = { k:getattr(rec,k) for k in fields if k != 'in_sla'}
        if card['in_support_sla'] and card['in_response_sla'] :
            results += 'Case: %s\t%s' % (card['number'], card['subject']) + '\n'
        elif not card['in_response_sla']:
            results += 'Case: %s\t%s' %(card['number'], card['subject']) + '\n'
            results+= 'System: %s\tPriority: %s\tTarget Response: %.2fh\tActual: %.2fh' %(
                card[OUT_SLA_VIEW_DETAILS[sfdc][0]], card[OUT_SLA_VIEW_DETAILS[sfdc][1]],
                SLA_RESPONSE[sfdc], card['response_time'])
            results+= '\n'
        else:
            results += 'Case: %s\t%s' %(card['number'], card['subject']) + '\n'
            results+= 'System: %s\tPriority: %s\tTarget Response: %.2fh\tActual: %.2fh' %(
                card[OUT_SLA_VIEW_DETAILS[sfdc][0]], card[OUT_SLA_VIEW_DETAILS[sfdc][1]],
                card['support_sla'], card['support_time'])
            results+= '\n'
    results += '-------------------------------' + '\n'
    results += 'Cases closed in' + target_month_str + ':' + str(mo_len) + '\n'
    if mo_len > 0:
        results += "Out of support SLA count :" + str(syslabox['total']['out_sup_sla'])  + ", which is" + str(100.00*(syslabox['total']['out_sup_sla']/mo_len)) + "%"
        results += "Out of response SLA count:" + str(syslabox['total']['out_resp_sla']) + ", which is" + str(100.00*(syslabox['total']['out_resp_sla']/mo_len)) + "%"
        results += "Combined Out of SLA      :" + str(100.00*(syslabox['total']['combined']/mo_len)) + "%" + '\n'
    results += '-------------------------------' + '\n'
    results += "Count OUT_resp OUT_supp  --- system" + '\n'
    for sys in SYSTEMS[sfdc]:
        results += str(syslabox[sys]['count']) + '\t' + str(syslabox[sys]['out_resp_sla']) + '\t' + str(syslabox[sys]['out_sup_sla']) + '\t' + 'for system' + '\t' + sys + '\n'
    
    print(results)
    return render(request, 'results.html', {'title': 'Monthly Report', 'data': results})