# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Case'
        db.create_table('django2wrap_case', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('sfdc', self.gf('django.db.models.fields.CharField')(default='WLK', max_length=3)),
            ('system', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('status', self.gf('django.db.models.fields.CharField')(default='Open', max_length=6)),
            ('priority', self.gf('django.db.models.fields.CharField')(default='3', max_length=1)),
            ('reason', self.gf('django.db.models.fields.CharField')(default='Problem', max_length=64)),
            ('in_response_sla', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('in_resolution_sla', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('contact', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('closed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('target_resolution_sla', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('target_response_sla', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('resolution_time', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('response_time', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('link', self.gf('django.db.models.fields.URLField')(unique=True, max_length=200)),
            ('raw', self.gf('django.db.models.fields.TextField')()),
            ('postpone', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('postponedate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('target_chase', self.gf('django.db.models.fields.DateTimeField')()),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Agent'])),
            ('shift', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Shift'])),
        ))
        db.send_create_signal('django2wrap', ['Case'])

        # Adding model 'Comment'
        db.create_table('django2wrap_comment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('agent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Agent'], null=True, blank=True)),
            ('shift', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Shift'])),
            ('case', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Case'])),
            ('call', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Call'], null=True, blank=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('postpone', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('postponedate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('byclient', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('raw', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('django2wrap', ['Comment'])

        # Adding model 'Shift'
        db.create_table('django2wrap_shift', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('agent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Agent'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('color', self.gf('django.db.models.fields.CharField')(default='#ff0000', max_length=7)),
            ('tipe', self.gf('django.db.models.fields.CharField')(default='Morning', max_length=1)),
        ))
        db.send_create_signal('django2wrap', ['Shift'])

        # Adding model 'Call'
        db.create_table('django2wrap_call', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('agent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Agent'])),
            ('shift', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Shift'])),
            ('filename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('case', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django2wrap.Case'], null=True, blank=True)),
        ))
        db.send_create_signal('django2wrap', ['Call'])


    def backwards(self, orm):
        # Deleting model 'Case'
        db.delete_table('django2wrap_case')

        # Deleting model 'Comment'
        db.delete_table('django2wrap_comment')

        # Deleting model 'Shift'
        db.delete_table('django2wrap_shift')

        # Deleting model 'Call'
        db.delete_table('django2wrap_call')


    models = {
        'django2wrap.agent': {
            'Meta': {'object_name': 'Agent'},
            'current_color': ('django.db.models.fields.CharField', [], {'default': "'#ff0000'", 'max_length': '7'}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
        },
        'django2wrap.call': {
            'Meta': {'object_name': 'Call'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Agent']"}),
            'case': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Case']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'filename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shift': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Shift']"})
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
        'django2wrap.shift': {
            'Meta': {'object_name': 'Shift'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django2wrap.Agent']"}),
            'color': ('django.db.models.fields.CharField', [], {'default': "'#ff0000'", 'max_length': '7'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tipe': ('django.db.models.fields.CharField', [], {'default': "'Morning'", 'max_length': '1'})
        }
    }

    complete_apps = ['django2wrap']