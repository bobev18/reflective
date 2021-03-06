# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Resource.actions'
        db.delete_column('django2wrap_resource', 'actions')


    def backwards(self, orm):
        # Adding field 'Resource.actions'
        db.add_column('django2wrap_resource', 'actions',
                      self.gf('django.db.models.fields.CharField')(default=None, max_length=32),
                      keep_default=False)


    models = {
        'django2wrap.agent': {
            'Meta': {'object_name': 'Agent'},
            'current_color': ('django.db.models.fields.CharField', [], {'default': "'#ff0000'", 'max_length': '7'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "'support@reflective.com'", 'max_length': '75'}),
            'end': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'start': ('django.db.models.fields.DateField', [], {})
        },
        'django2wrap.call': {
            'Meta': {'object_name': 'Call'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['django2wrap.Agent']", 'null': 'True'}),
            'case': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Case']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'filename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shift': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['django2wrap.Shift']", 'null': 'True'})
        },
        'django2wrap.case': {
            'Meta': {'object_name': 'Case'},
            'closed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'contact': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Agent']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_resolution_sla': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'in_response_sla': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4'}),
            'postpone': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'postponedate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.CharField', [], {'default': "'3'", 'max_length': '1'}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'reason': ('django.db.models.fields.CharField', [], {'default': "'Problem'", 'max_length': '64'}),
            'resolution_time': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'response_time': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'sfdc': ('django.db.models.fields.CharField', [], {'default': "'WLK'", 'max_length': '3'}),
            'shift': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Shift']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Open'", 'max_length': '6'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'system': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'target_chase': ('django.db.models.fields.DateTimeField', [], {}),
            'target_resolution_sla': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'target_response_sla': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'django2wrap.comment': {
            'Meta': {'object_name': 'Comment'},
            'added': ('django.db.models.fields.DateTimeField', [], {}),
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Agent']", 'null': 'True', 'blank': 'True'}),
            'byclient': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'call': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Call']", 'null': 'True', 'blank': 'True'}),
            'case': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Case']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'postpone': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'postponedate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'shift': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Shift']"})
        },
        'django2wrap.resource': {
            'Meta': {'object_name': 'Resource'},
            'class_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {}),
            'module': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'django2wrap.shift': {
            'Meta': {'unique_together': "(('date', 'tipe'),)", 'object_name': 'Shift'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Agent']"}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#ff0000'", 'max_length': '7'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tipe': ('django.db.models.fields.CharField', [], {'default': "'Morning'", 'max_length': '7'})
        }
    }

    complete_apps = ['django2wrap']