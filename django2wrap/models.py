from django.db import models
from django.db.models import Max
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

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Agent(models.Model):
    name = models.CharField(max_length=30)
    start = models.DateField()
    end = models.DateField()
    current_color = models.CharField(max_length=7, choices=AGENT_COLORS, default='#ff0000')
    email = models.EmailField(default='support@reflective.com')

    class Meta:
        unique_together = (("name", "start"),)
    
    def __str__(self):
        return self.name

class Shift(models.Model):
    agent = models.ForeignKey(Agent)
    date = models.DateTimeField(unique=True)
    color = models.CharField(max_length=7, choices=AGENT_COLORS, default='#ff0000')
    tipe = models.CharField(max_length=7, choices=(('Morning', 'Morning'), ('Middle', 'Middle'), ('Late', 'Late')), default='Morning')
    # TODO: add type "overtime" and "return" ; to allow for few hrs, add shiftlenth

    class Meta:
        unique_together = (("date", "tipe"),)

    def __str__(self):
        return self.date.strftime("%d/%m/%y %H:%M") + ':' + self.tipe

    def items(self):
        return [self.agent.name, self.date.strftime("%d/%m/%y %H:%M"), self.tipe,] # self.color]

class Contact(models.Model):
    name = models.CharField(max_length=64)
    sfdc = models.CharField(max_length=3, choices=SFDC_ACCOUNTS)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    link = models.URLField()

    class Meta:
        unique_together = (("sfdc", "link"),)
    
    def __str__(self):
        return self.name + ' ' + self.email + ' in ' + self.sfdc

class Case(models.Model):
    #'status', 'actual', 'name', 'created', 'udata', 'system', 'sla', 'reason', 'link', 'result', 'closed', 'casetimes', 'closedate', 'problem', 'subject', 'id', 'severity'
    number = models.CharField(max_length=4) #id
    subject = models.CharField(max_length=1024) #subject
    description = models.TextField() #problem
    sfdc = models.CharField(max_length=3, choices=SFDC_ACCOUNTS, default='WLK')
    # we want system to be dependant on SFDC, but the place for such dependancy is in the UI task,
    ## not DB => in DB we push a mix
    #### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ####
    #### The proper approach might be to have separate clases for the different SFDC accounts
    ######### I will try it with a mix, and plan to refactor them later...
    # system = models.CharField(max_length=3, choices=ALL_SYSTEMS, default='WLK') #system
    system = models.CharField(max_length=64) #system
    status = models.CharField(max_length=6, choices=STATUSES, default='Open') #status
    priority = models.CharField(max_length=1, choices=PRIORITIES, default='3') #severity
    reason = models.CharField(max_length=64, choices=REASONS, default='Problem', blank=True, null=True) #reason
    # problem = models.CharField(max_length=64, choices=, default='', blank=True, null=True) #problem
    created = models.DateTimeField() #created
    closed = models.DateTimeField(null=True) #closedate
    link = models.URLField() # link ## unique ~~ what if 2 contact from WLK and RSL have matching link strings

    in_support_sla = models.BooleanField(default=True) # actual
    in_response_sla = models.BooleanField(default=True) # actual
    support_sla = models.PositiveIntegerField() # sla # in hrs
    response_sla = models.FloatField() # sla # in hrs
    support_time = models.FloatField(null=True) # casetimes ## resolution time in hrs
    response_time = models.FloatField(null=True) # casetimes ## response time in hrs
    # raw = models.TextField(null=True) # this should be added once on stable DB
    
    postpone = models.DateTimeField(null=True)
    target_chase = models.DateTimeField()
    chased = models.BooleanField(default=True) # actual

    contact =  models.ForeignKey(Contact)
    creator = models.ForeignKey(Agent)
    shift = models.ForeignKey(Shift) # the shift during which the case was created
    last_sync = models.DateTimeField(auto_now_add=True)
    ###
    ### list of comments of a case would be the reversed call on the Comment>>>Case via foreign key
    ### 
    class Meta:
        unique_together = (("sfdc", "number"),("sfdc", "link"),)

    def __str__(self):
        return self.number

    def last_comment(self):
        comments = Comment.objects.filter(case=self).order_by('-added')
        if len(comments) > 0:
            # maxdate = comments.aggregate(Max('added'))['added__max']
            # return Comment.objects.get(case=self, added=maxdate).txt()
            # return comments[].txt()
        # elif len(comments) == 1:
            return comments[0].txt()
        else:
            return 'n/a'

    def comments(self):
        return Comment.objects.filter(case=self).order_by('added')

class SupportEmail(models.Model):
    uid = models.CharField(max_length=12, unique=True)
    subject = models.CharField(max_length=1024)
    date = models.DateTimeField() # unique=True ??
    sender = models.EmailField()
    recipient = models.EmailField()
    message = models.TextField()
    sfdc = models.CharField(max_length=3, choices=SFDC_ACCOUNTS, default=None, null=True)
    agent = models.ForeignKey(Agent, blank=True, null=True)
    shift = models.ForeignKey(Shift, blank=True, null=True)
    case = models.ForeignKey(Case, blank=True, null=True)
    contact =  models.ForeignKey(Contact, default=None, null=True)

    # class Meta:
    #     unique_together = (("date", "subject"),)

    def __str__(self):
        return self.uid + ' ' + self.date.strftime("%d/%m/%Y %H:%M") + ' : ' + self.subject

class Call(models.Model):
    agent = models.ForeignKey(Agent, default=None, null=True) # needed until I include the schedule from before Dec 2012
    shift = models.ForeignKey(Shift, default=None, null=True) # needed until I include the schedule from before Dec 2012
    case = models.ForeignKey(Case, blank=True, null=True)
    filename = models.CharField(max_length=128, unique=True)
    date = models.DateTimeField()
    contact =  models.ForeignKey(Contact, default=None, null=True)
    # contact = models.CharField(max_length=128, default=None, null=True)
        
    def __str__(self):
        return self.filename

    # def wipe_table(self):
    #     # this is needed to overcome bug: https://code.djangoproject.com/ticket/16426
    #     # use Call.wipe_table() instead of Call.objects.all().delete()
    #     cursor = connection.cursor()
    #     table_name = self.model._meta.db_table
    #     sql = "DELETE FROM %s;" % (table_name, )
    #     cursor.execute(sql)

    def items(self):
        if self.agent:
            agent_name = self.agent.name
        else:
            agent_name = 'n/a'

        play_button = '<a href="/listen/' + str(self.id) + '/" target="_blank">&#9658;</a>'
        return [play_button, self.filename, agent_name, self.date.strftime("%d/%m/%y"), self.case,] #self.shift.date]

class Comment(models.Model):
    agent = models.ForeignKey(Agent, null=True)
    # client = models.ForeignKey(Client, null=True) 
    byclient = models.BooleanField(default=False) #this will fall once we have Client model
    shift = models.ForeignKey(Shift)
    case = models.ForeignKey(Case)
    call = models.ForeignKey(Call, default=None, null=True)
    email = models.ForeignKey(SupportEmail, default=None, null=True)
    added = models.DateTimeField()
    message = models.TextField()
    # postpone = models.BooleanField(default=False) # lacking the DateTime field is indication of no postpone
    postpone = models.DateTimeField(null=True)
    
    def __str__(self):
        return str(self.case) + ': ' + str(self.added)

    def txt(self):
        if self.byclient:
            return self.added.strftime("%d/%m/%Y %H:%M") + ' client: '+self.message
            # return self.client+':'+self.message
        else:
            return self.added.strftime("%d/%m/%Y %H:%M") + ' ' + str(self.agent)+': '+self.message

class Resource(models.Model):
    name = models.CharField(max_length=32)
    last_sync = models.DateTimeField()
    module = models.CharField(max_length=125) # may use use it as name of path-name
    class_name = models.CharField(max_length=30) # the class name may be different from the module name
    # last_sync_fields = ? DictField
    #   I need event log, to store info on what update was pushed when, and how up-to-date is every subset of the DB
    #   or I can add "creation timestamp" for each record
    #   actually I don't need that for any record besides Cases ...and maybe Schedule
    
    def __str__(self):
        return self.name
