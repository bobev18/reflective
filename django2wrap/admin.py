from django.contrib import admin
# from mysite.books.models import Publisher, Author, Book
from django2wrap.models import Agent, Shift, Case, Call, Comment, Resource

from django.contrib.admin import DateFieldListFilter

class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'start', 'end', 'current_color', 'email')
    search_fields = ('name', 'start', 'end', 'current_color', 'email')

class ShiftAdmin(admin.ModelAdmin):
    list_display = ('agent', 'date', 'color', 'tipe')
    list_filter = (
        ('date', DateFieldListFilter),
    )
    search_fields = ('agent__name', 'date', 'color', 'tipe')

class CaseAdmin(admin.ModelAdmin):
    list_display = ('number', 'subject', 'description', 'sfdc', 'system', 'status', 'priority', 'reason', 'in_response_sla', 'in_support_sla', 'contact', 'created', 'closed', 'support_sla',
        'response_sla', 'support_time', 'response_time', 'link', 'postpone', 'target_chase', 'chased', 'creator', 'shift') # , 'raw')
    search_fields = ('number', 'subject', 'description', 'sfdc', 'system', 'status', 'priority', 'reason', 'in_response_sla', 'in_support_sla', 'contact', 'created', 'closed', 'support_sla',
        'response_sla', 'support_time', 'response_time', 'link', 'postpone', 'target_chase', 'chased', 'creator__name', 'shift__date') # , 'raw')

class CallAdmin(admin.ModelAdmin):
    list_display = ('agent', 'shift', 'case', 'filename', 'date')
    search_fields = ('agent__name', 'shift__date', 'case__number', 'filename', 'date')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('agent', 'shift', 'case', 'call', 'added', 'message', 'postpone', 'byclient')
    search_fields = ('agent__name', 'shift__date', 'case__number', 'call__filename', 'added', 'message', 'postpone', 'byclient')

class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_sync', 'module', 'class_name')
    search_fields = ('name', 'last_sync', 'module', 'class_name')

admin.site.register(Agent, AgentAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Call, CallAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Resource, ResourceAdmin)

