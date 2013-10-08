import os
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail, mail_admins, mail_managers, EmailMessage, EmailMultiAlternatives
from email.mime.multipart import MIMEBase
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django2wrap.forms import EscalationForm, LicenseForm
from django2wrap.models import Agent, Shift, Case, Call, Comment, Resource
import django2wrap.shifts as shifts
import django2wrap.calls as phonecalls

ESCALATION_CONTACTS = ['Vess <vesselin.drangajov@reflective.com>', 'Graham <graham.parsons@reflective.com>', 'Iliyan <iliyan@reflectivebg.com>', 'Support <support@reflective.com>']
LICENSE_CONTACTS = ['License Department <licenserequest@reflective.com>', 'Iliyan <iliyan@reflectivebg.com>', 'Support <support@reflective.com>']

ESCALATION_MESSAGE_BODY = """<html>
<style>
body{
font-family:\"Lucida Grande\", \"Lucida Sans Unicode\", Verdana, Arial, Helvetica, sans-serif;
font-size:10px;
}
p, h1, form, button { border:0; margin:0; padding:0; }
</style>
<body>
<div id=\"stylized\" class=\"myblock\">
<h1>Escalation</h1>
<table style="padding:5px;">
<tr><td><label>Submitted by</label></td><td>*agent*</td></tr>
<tr><td><label>Case</label></td><td>*case*</td></tr>
<tr><td><label>Priority</label></td><td>*priority*</td></tr>
<tr><td><label>Company</label></td><td>*company*</td></tr>
<tr><td><label>Contact</label></td><td>*contact*</td></tr>
<tr><td><label>Description</label></td><td>*description*</td></tr>
<tr><td><label>Investigated</label></td><td>*investigated*</td></tr>
</table>
</div>
</body>
</html>"""

def homepage(request):
    return HttpResponse('<html><body>Welcome<br><br><a href="/chase/">Chaser</a><br><a href="https://78.142.1.136/mwiki/">Wiki</a><br><a href="/escalation/">Escalation Form</a><br><a href="/license/">License Form</a></body></html>')

def escalation_form(request):
    if request.method == 'POST':
        form = EscalationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            subject = "escalation case: " + cd['case'] + " priority: " + cd['priority']
            message = ESCALATION_MESSAGE_BODY
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
                to = ESCALATION_CONTACTS
            mymail = EmailMultiAlternatives(subject, message, 'Support <support@reflective.com>', to, headers = {'Reply-To': 'support@reflective.com'})
            mymail.attach_alternative(message, 'text/html')
            mymail.send(fail_silently=False)
            return HttpResponseRedirect('/')
    else:
        form = EscalationForm()
    return render(request, 'escalation_form.html', {'form': form})

LICENSE_MESSAGE_BODY = """<html>
<style>
body{
font-family:\"Lucida Grande\", \"Lucida Sans Unicode\", Verdana, Arial, Helvetica, sans-serif;
font-size:10px;
}
p, h1, form, button { border:0; margin:0; padding:0; }
</style>
<body>
<div id=\"stylized\" class=\"myblock\">
<h1>License Request</h1>
<table style="padding:5px;">
<tr><td><label>Submitted by</label></td><td>*agent*</td></tr>
<tr><td><label>Case</label></td><td>*case*</td></tr>
<tr><td><label>Priority</label></td><td>*priority*</td></tr>
<tr><td><label>Requestor organization type</label></td><td>*requestor*</td></tr>
<tr><td><label>Company</label></td><td>*company*</td></tr>
*Partner Company*
<tr><td><label>Contact</label></td><td>*contact*</td></tr>
<tr><td><label>HostID</label></td><td>*hostid*</td></tr>
<tr><td><label>Product</label></td><td>*product*</td></tr>
<tr><td><label>Type</label></td><td>*licensetype*</td></tr>
*period*
<tr><td><label>License Status</label></td><td>*licensestatus*</td></tr>
<tr><td><label>License Function</label></td><td>*licensefunction*</td></tr>
*notes*
</table>
</div>
</body>
</html>"""

def license_form(request):
    if request.method == 'POST':
        form = LicenseForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            subject = "license request case: " + cd['case'] + " priority: " + cd['priority']
            message = LICENSE_MESSAGE_BODY
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
                to = LICENSE_CONTACTS

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


def listen(request, agent = 'Boris', file_name = '+000000_2012.06.15.Fri.17.40.37.mp3'):
    # note that MP3_STORAGE should not be in MEDIA_ROOT
    fname = os.path.join(settings.MP3_STORAGE, agent, file_name)
    f = open(fname, "rb")
    response = HttpResponse()
    response.write(f.read())
    response['Content-Type'] = 'audio/mp3'
    response['Content-Length'] = os.path.getsize(fname)
    return response

def sync(request):
    systems = ['shifts', 'calls']
    actions = ['Sync', 'View', 'Wipe'] #make this Meta -- passing to form and to coresponding method
    resources = Resource.objects.all()
    if request.method == 'POST':
        # form = ()
        # cd = form.cleaned_data
        sys = request.POST['system']
        action = request.POST['action']
        # print('sys', sys)
        if sys == 'shifts':
            sched = shifts.Shifts()
            if action == 'Sync':
                sched.wipe_db()
                sched.download_data(**GLOGIN)
                sched.save_db_data()
                results = sched.data
            elif action == 'View':
                results = [ z.items() for z in Shift.objects.all() ]
                results.insert(0,['Name', 'date time', 'Type', 'Color Code',])
            elif action == 'Wipe':
                sched.wipe_db()
            else:
                errors = ['no such action']
        elif sys == 'calls':
            listing = phonecalls.Calls()
            if action == 'Sync':
                listing.wipe_db()
                listing.load()
                results = listing.data
                listing.save_db_data()
            elif action == 'View':
                results = Call.objects.all()
            elif action == 'Wipe':
                listing.wipe_db()
            else:
                errors = ['no such action']
        else:
            errors = ['no such system']
            
    return render(request, 'sync.html', locals())