from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django2wrap.models import Agent, Resource #, Shift, Case, Call, Comment
import django.utils.timezone as timezone

TYPE_CHOICES = (('Permanent', 'Permanent (full)'), ('Rental', 'Rental'), ('Standard Trial', 'Standard Trial'), ('Non Standard Trial', 'Non Standard Trial'), ('Consultant Annual', 'Consultant Annual'), ('Project', 'Project'), ('Non-commercial', 'Non-commercial'))
STATUS_CHOICES = (
    ('table shows TBC that matches the request', 'table shows TBC that matches the request'), 
    ('table doesn\'t show TBC or HostID matching the request', 'table doesn\'t show TBC or HostID matching the request'), 
    ('table shows that the license exists and there is a HostID allocated', 'table shows that the license exists and there is a HostID allocated'), 
    ('there is no TBC or HostID that matches the request', 'there is no TBC or HostID that matches the request'), 
)
FUNCTION_CHOICES = ( ('Designer','Designer'), ('Viewer','Viewer'), ('Controller','Controller'), ('Monitor','Monitor'), )

class EscalationForm(forms.Form):
    agent = forms.ChoiceField(choices=tuple(set( (z.name,z.name) for z in Agent.objects.filter(end__gt=timezone.now()))), help_text='Select your name')
    case = forms.CharField(min_length=4, max_length=4, label='Case Number', help_text='Enter the last four digist of the SFDC case number')
    priority = forms.ChoiceField(choices=(('normal', 'normal'), ('high', 'high')), help_text='Add support priority')
    company = forms.CharField(max_length=128, help_text='Add company name')
    contact = forms.CharField(max_length=64, help_text='Add contact name')
    description = forms.CharField(widget=forms.Textarea, help_text='Add case / problem description')
    investigated = forms.CharField(widget=forms.Textarea, help_text='Add what have you attempted / investigated')

class LicenseForm(forms.Form):
    agent = forms.ChoiceField(choices=tuple(set( (z.name,z.name) for z in Agent.objects.filter(end__gt=timezone.now()))), help_text='Select your name')
    case = forms.CharField(min_length =4, max_length=4, label='Case Number', help_text='Enter the last four digist of the SFDC case number')
    priority = forms.ChoiceField(choices=(('normal', 'normal'), ('high', 'high')), help_text='Add support priority')
    requestor = forms.ChoiceField(widget=forms.RadioSelect, choices=(('partner', 'partner'), ('client of a partner', 'client of a partner'), ('end user', 'end user')), label='Organization Type', help_text='Select requestor type')
    company = forms.CharField(max_length=128, help_text='Add the company name')
    partner_company = forms.CharField(max_length=128, help_text='Partner company name (optional - applies only if Organization type is "Clent of a Partner")', required=False)
    contact = forms.CharField(max_length=64, help_text='Add contact name')
    hostid = forms.CharField(min_length =6, max_length=6, label='Host ID', help_text='Enter the Host ID')
    product = forms.ChoiceField(choices=(('StressTester', 'StressTester'), ('Sentinel', 'Sentinel')), help_text='What product is the license for')
    license_type = forms.ChoiceField(choices=TYPE_CHOICES, help_text='What license type is requested')
    period = forms.IntegerField(help_text='period of the license in days(optional - applies for trial license type', required=False)
    license_status = forms.ChoiceField(widget=forms.RadioSelect, choices=STATUS_CHOICES, help_text='Depends on what shows in the license table under the client in SFDC', label='License Status')
    license_function = forms.ChoiceField(choices=FUNCTION_CHOICES, help_text='What is the license function', label='License Function')
    notes = forms.CharField(widget=forms.Textarea, help_text='Notes (optional)', required=False)
    host_id_change_form = forms.FileField(widget=forms.FileInput, label='HostID Change Request Form', help_text='Change request form signed by the client (optional)', required=False)

class SyncDetailsForm(forms.Form):
    # actions = forms.ChoiceField(choices=tuple( (z,z) for z in ['Update', 'View', 'Reload'] ))
    ## dont use actions as a dopdown box -- it's rendered as separate submit buttons.
    ### TODO: make my own form.Field that handles the above situation.
    system = forms.ChoiceField(choices=tuple( (z.name,z.name) for z in Resource.objects.all() ), help_text='Resource')
    agent = forms.ChoiceField(choices=((None, '-----'),) + tuple(set( (z.name,z.name) for z in Agent.objects.all() )), help_text='Agent', required=False, initial=None)
    from_date = forms.DateField(widget=SelectDateWidget(years = tuple( str(z + 2010) for z in range(4) )), required=False)
    # to_date = forms.DateField(widget=SelectDateWidget(years = set( str(z + 2010) for z in range(4) )), required=False)

class WeeklyForm(forms.Form):
    from_date = forms.DateField(widget=SelectDateWidget(years=(2013,)), required=False)