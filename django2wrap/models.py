from django.db import models
import django.utils.timezone as timezone


SFDC_ACCOUNTS = (('WLK', 'Wightlink'), ('RSL', 'Reflective Solutions'),)
WLK_SYSTEM = (
    ('BBS', 'Blackberry Server'),
    ('CDI', 'CDI'),
    ('CRM', 'CRM'),
    ('DOC', 'Document Management'),
    ('DRS', 'DRS'),
    ('EML', 'Email'),
    ('FE+', 'Ferry+'),
    ('GP ', 'Great Plains'),
    ('RAN', 'Intranet'),
    ('LPC', 'Local PC'),
    ('RTS', 'Profit Optimisation (RTS)'),
    ('RPO', 'RPO','Sailing Statistics (AIS)'),
    ('WAN', 'Wide Area Network'),
    ('SEN', 'Sentinel'),
    ('NL ', 'NiceLabel'),
)
ST_SYSTEM = ( # maps to Product ?
    ('')
)
STATUSES = (('Open', 'Open'), ('Closed', 'Closed'),)
PRIORITIES = (('1', 'High'), ('2', 'Normal'), ('3', 'Low'),)
WLK_REASONS = (('Problem', 'Problem'), ('Question', 'Question'), ('Request', 'Request'), ('System Down', 'System Down'), ('Incident', 'Incident'), ('Alert', 'Alert'),)
RSL_REASONS = (('Problem', 'Problem'), ('Question', 'Question'), ('Feature Request', 'Feature Request'),)
REASONS = tuple(set(WLK_REASONS + RSL_REASONS))
AGENT_COLORS = ( 
    ('#ff0000', 'red'),
    ('#00ff00', 'green'),
    ('#0000ff', 'blue'),
    ('#ffff00', 'yellow'),
)

class Agent(models.Model):
    name = models.CharField(max_length=30)
    start = models.DateField()
    end = models.DateField()
    current_color = models.CharField(max_length=7, choices=AGENT_COLORS, default='#ff0000')
    email = models.EmailField(default='support@reflective.com')
    
    def __str__(self):
        return self.name

class Shift(models.Model):
    agent = models.ForeignKey(Agent)
    date = models.DateTimeField()
    color = models.CharField(max_length=7, choices=AGENT_COLORS, default='#ff0000')
    tipe = models.CharField(max_length=7, choices=(('Morning', 'Morning'), ('Middle', 'Middle'), ('Late', 'Late')), default='Morning')

    def __str__(self):
        return str(self.date) + ':' + self.tipe

    def items(self):
        return [self.agent.name, timezone.make_aware(self.date, timezone.get_current_timezone()).strftime("%d/%m/%y %H:%M"), self.tipe, self.color]

class Case(models.Model):
    #'status', 'actual', 'name', 'created', 'udata', 'system', 'sla', 'reason', 'link', 'result', 'closed', 'casetimes', 'closedate', 'problem', 'subject', 'id', 'severity'
    number = models.CharField(max_length=4, unique=True) #id
    subject = models.CharField(max_length=1024) #subject
    description = models.TextField() #problem

    sfdc = models.CharField(max_length=3, choices=SFDC_ACCOUNTS, default='WLK')
    # we want system to be dependant on SFDC, but that UI task, not DB => in DB we push a mix
    #### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ####
    #### The proper approach might be to have separate clases for the different SFDC accounts
    ######### I will try it with a mix, and plan to refactor that later...
    # system = models.CharField(max_length=3, choices=ALL_SYSTEMS, default='WLK') #system
    system = models.CharField(max_length=64) #system
    status = models.CharField(max_length=6, choices=STATUSES, default='Open') #status
    priority = models.CharField(max_length=1, choices=PRIORITIES, default='3') #severity
    reason = models.CharField(max_length=64, choices=REASONS, default='Problem') #reason

    in_response_sla = models.BooleanField(default=True) # actual
    in_resolution_sla = models.BooleanField(default=True) # actual

    contact =  models.CharField(max_length=64) #===name #only the name for now...
    created = models.DateTimeField() #created
    closed = models.DateTimeField(null=True) #closedate

    target_resolution_sla = models.PositiveIntegerField() # sla # in hrs
    target_response_sla = models.PositiveIntegerField() # sla # in hrs
    resolution_time = models.FloatField(null=True) # casetimes ## resolution time in hrs
    response_time = models.FloatField(null=True) # casetimes ## response time in hrs
    link = models.URLField(unique=True) # link
    raw = models.TextField() # udata
    
    postpone = models.BooleanField(default=False)
    postponedate = models.DateTimeField(blank=True, null=True)
    target_chase = models.DateTimeField()

    creator = models.ForeignKey(Agent)
    shift = models.ForeignKey(Shift) # the shift during which the case was created
    ###
    ### list of comments of a case would be the reversed call on the Comment>>>Case via foreign key
    ### 

    def __str__(self):
        return self.number

class Call(models.Model):
    agent = models.ForeignKey(Agent)
    shift = models.ForeignKey(Shift)
    case = models.ForeignKey(Case, blank=True, null=True)
    filename = models.CharField(max_length=128, unique=True)
    date = models.DateTimeField()
        
    def __str__(self):
        return self.filename

class Comment(models.Model):
    agent = models.ForeignKey(Agent, blank=True, null=True)
    shift = models.ForeignKey(Shift)
    case = models.ForeignKey(Case)
    call = models.ForeignKey(Call, blank=True, null=True)
    # email_message = models.ForeignKey(EmailMessage)
    added = models.DateTimeField()
    message = models.TextField()
    postpone = models.BooleanField(default=False)
    postponedate = models.DateTimeField(blank=True, null=True)
    byclient = models.BooleanField(default=False)
    raw = models.TextField() # udata
    
    def __str__(self):
        return self.case + ': ' + str(self.added)


class Resource(models.Model):
    name = models.CharField(max_length=30)
    last_sync = models.DateTimeField() # last full sync
    
    def __str__(self):
        return self.name
