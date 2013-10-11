import os
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail, mail_admins, mail_managers, EmailMessage, EmailMultiAlternatives
from email.mime.multipart import MIMEBase
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django2wrap.forms import EscalationForm, LicenseForm, SyncDetailsForm
from django2wrap.models import Agent, Shift, Case, Call, Comment, Resource
import django2wrap.shifts as shifts
# import django2wrap.calls# as phonecalls
from django2wrap.calls import PhoneCalls # as phonecalls


def homepage(request):
    return HttpResponse('<html><body>Welcome<br><br><a href="/chase/">Chaser</a><br><a href="https://78.142.1.136/mwiki/">Wiki</a><br><a href="/escalation/">Escalation Form</a><br><a href="/license/">License Form</a></body></html>')

def escalation_form(request):
    if request.method == 'POST':
        form = EscalationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            subject = "escalation case: " + cd['case'] + " priority: " + cd['priority']
            message = settings.ESCALATION_MESSAGE_BODY
            message = message.replace("*agent*", cd['agent'])
            message = message.replace("*case*", cd['case'])
            message = message.replace("*priority*", cd['priority'])
            message = message.replace("*company*", cd['company'])
            message = message.replace("*contact*", cd['contact'])
            message = message.replace("*description*", cd['description'])
            message = message.replace("*investigated*",cd['investigated'])
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
            message = message.replace("*agent*", cd['agent'])
            message = message.replace("*case*", cd['case'])
            message = message.replace("*priority*", cd['priority'])
            message = message.replace("*requestor*", cd['requestor'])
            message = message.replace("*company*", cd['company'])
            if cd['pather_company']:
                message = message.replace("*Partner Company*", "<tr><td><label>Client</label></td><td>%s</td></tr>" % cd['pather_company'])
            else:
                message = message.replace("*Partner Company*", '')
            message = message.replace("*contact*", cd['contact'])
            message = message.replace("*hostid*", cd['hostid'])
            message = message.replace("*product*", cd['product'])
            message = message.replace("*licensetype*", cd['license_type'])
            message = message.replace("*licensetype*", cd['license_type'])
            if cd['period']:
                message = message.replace("*period*", "<tr><td><label>Period</label></td><td>%s</td></tr>" % cd['period'])
            else:
                message = message.replace("*period*", '')
            message = message.replace("*licensestatus*", cd['status'])
            message = message.replace("*licensefunction*", cd['function'])
            if cd['period']:
                message = message.replace("*notes*", "<tr><td><label>Notes</label></td><td>%s</td></tr>" % cd['notes'])
            else:
                message = message.replace("*notes*", '')

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
    actions = ['Update', 'View', 'Reload'] #make this Meta -- passing to form and to coresponding method getattr(foo, 'bar')()
    # update - pull specific subset of a resourse, add the new ones, and update old records in db
    #   update would need more form fields (agent, time period[hour,day,week, month], )
    # view   - show records from db - may use same subset fields as in "update"
    # reload - empty db, pull all records from resourse, and save them to db
    # load   - (basic) pull all records from resourse
    # wipe   - (basic) empty db
    # save   - (basic) save the data to db

    if request.method == 'POST':
        form = SyncDetailsForm(request.POST)
        if form.is_valid():
            clean_data = form.cleaned_data
            if clean_data['agent'] == 'None':
                clean_data['agent'] = None
            if clean_data['from_date']:
                clean_data['from_date'] = datetime(*tuple( getattr(clean_data['from_date'], z) for z in ['year', 'month', 'day'] ))
            sys = clean_data['system']
            action = request.POST['action']
            # print('sys', sys)
            if sys == 'shifts':
                sched = shifts.Shifts()
                if action == 'Reload':
                    sched.wipe_db()
                    sched.download_data(**settings.GLOGIN)
                    sched.save_db_data()
                    results = sched.data
                elif action == 'Update':
                    pass
                elif action == 'View':
                    results = [ z.items() for z in Shift.objects.all() ]
                    results.insert(0, ['Name', 'date time', 'Type',]) # 'Color Code',])
                # elif action == 'Wipe':
                #     sched.wipe_db()
                else:
                    errors = ['no such action']
            elif sys == 'calls':
                listing = PhoneCalls()
                print('clean_data', clean_data)
                if action == 'Reload':
                    results = listing.reload()
                elif action == 'Update':
                    results = listing.update(clean_data['agent'], clean_data['from_date'])
                elif action == 'View':
                    results = listing.view(clean_data['agent'], clean_data['from_date'])
                    
                # elif action == 'Wipe':
                #     listing.wipe_db()
                else:
                    errors = ['no such action']
            else:
                errors = ['no such system']
            
    else:
        form = SyncDetailsForm()
    return render(request, 'sync.html', locals())

    # resources = Resource.objects.all()
    # agents = Agent.objects.all()
    # # resources = ['Shift', 'Call']
    # if request.method == 'POST':
    #     # form = ()
    #     # cd = form.cleaned_data
    # return render(request, 'sync.html', locals())            