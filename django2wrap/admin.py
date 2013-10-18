from django.contrib import admin
# from mysite.books.models import Publisher, Author, Book
from django2wrap.models import Agent, Shift, Case, Call, Comment, Resource

class AgentAdmin(admin.ModelAdmin):
   list_display = ('name', 'start', 'end', 'current_color', 'email')

class ShiftAdmin(admin.ModelAdmin):
   list_display = ('agent', 'date', 'color', 'tipe')

class CaseAdmin(admin.ModelAdmin):
   list_display = ('number', 'subject', 'description', 'sfdc', 'system', 'status', 'priority', 'reason', 'in_response_sla', 'in_support_sla', 'contact', 'created', 'closed', 'support_sla',
    'response_sla', 'support_time', 'response_time', 'link', 'postpone', 'postponedate', 'target_chase', 'creator', 'shift') # , 'raw')

class CallAdmin(admin.ModelAdmin):
   list_display = ('agent', 'shift', 'case', 'filename', 'date', 'case')

class CommentAdmin(admin.ModelAdmin):
   list_display = ('agent', 'shift', 'case', 'call', 'added', 'message', 'postpone', 'postponedate', 'byclient', 'raw')

class ResourceAdmin(admin.ModelAdmin):
   list_display = ('name', 'last_sync', 'module', 'class_name')

admin.site.register(Agent, AgentAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Call, CallAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Resource, ResourceAdmin)

