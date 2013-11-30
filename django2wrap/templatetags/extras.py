from django import template
import re

register = template.Library()

class TableMakerNode(template.Node):
    def __init__(self, var_to_be_presented_as_table, table_params): #later add class name for the table, so it can be CSSed
        self.target = template.Variable(var_to_be_presented_as_table)
        self.table_params = table_params

    def render(self, context):
        try:
            target = self.target.resolve(context) #should be list of lists
            html = '<table '+ self.table_params +'><tr>'
            # headers = target.pop(0) # not sure if pop is mutes the root object
            header = target[0]
            for name in header:
                html += '<th '+ self.table_params +'>' + str(name) + '</th>'
            html += '</tr>'
            for row in target[1:]:
                html += '<tr>'
                for val in row:
                    html += '<td '+ self.table_params +'>' + str(val) + '</td>'
                html += '</tr>'
            html += '</table>'

            return html
        except template.VariableDoesNotExist:
            return ''

@register.tag
def table_it(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, variable_name, table_params = token.split_contents()
    except ValueError:
        try:
            tag_name, variable_name = token.split_contents()
            table_params = '""'
        except ValueError:
            msg = '%r tag requires arguments' % token.split_contents()[0]
            raise template.TemplateSyntaxError(msg)

    if not (table_params[0] == table_params[-1] and table_params[0] in ('"', "'")):
        msg = "%r tag's argument should be in quotes" % tag_name
        raise template.TemplateSyntaxError(msg)
    
    return TableMakerNode(variable_name, table_params[1:-1])


def listify(table):
    header = None
    if isinstance(table, list):
        header = table[0]
        if isinstance(header, list):
            # [ [name, phone, company, email], [John, 055555555, Tesco, john@tesco.co.uk], [Brian, 888888888, Acme, brian@acme.biz]]
            body = table[1:]
        elif isinstance(header, dict):
            # [ {name: 'John', phone: '055555555', company: 'Tesco', email: john@tesco.co.uk}, {name: Brian, phone: 888888888, company: Acme, email: brian@acme.biz}]
            header = table[0].keys()
            body = [ z.values() for z in table ]
        elif isinstance(header, str):
            body = table
            header = None
        else:
            raise TypeError(table)
    elif isinstance(table, dict):
        # {name: [John, Brian], phone: [055555555, 888888888], company: [Tesco, Acme], email: [john@tesco.co.uk, brian@acme.biz]}
        header = table.keys()
        body = list(table.values())
        for i in range(len(body)):
            if not isinstance(body[i], list):
                body[i] = [body[i]]
    elif isinstance(table, str):
        # just lines of text with separator in [',', ';', '|', '\t']
        k = table.find('\n')
        header = max([ table[:k].split(z) for z in [',', ';', '|', '\t'] ], key=len) 
        # body = [ z.split() for z in table[k:].split('\n') ]
        body = [ max([ z.split(y) for y in [',', ';', '|', '\t'] ], key=len) for z in table[k+1:].split('\n') ]
    else:
        raise TypeError(table)

    return header, body

@register.simple_tag
def simple_table(table):
    try:
        header, body = listify(table)
    except TypeError:
        return ''
    try:
        html = '<table id="simpletable"><tr>'
        if header:
            for name in header:
                html += '<th>' + str(name) + '</th>'
            html += '</tr>'
        for row in body:
            html += '<tr>'
            for val in row:
                if type(val) == tuple:
                    html += '<td style="background-color:' + val[1]+';">' + str(val[0]) + '</td>'
                else:
                    html += '<td>' + str(val) + '</td>'
            html += '</tr>'
        html += '</table>'
        return html
    except template.VariableDoesNotExist:
        return ''
    except TypeError:
        return ''

@register.simple_tag
def schedule_table(table):
    try:
        header, body = listify(table)
    except TypeError:
        return ''
    try:
        html = '<table id="simpletable"><tr>'
        if header:
            for name in header:
                html += '<th>' + str(name) + '</th>'
            html += '</tr>'
        for row in body:
            html += '<tr>'
            for val in row:
                bgcolor = re.search('#[0-9a-f]{6}',str(val))
                if bgcolor:
                    html += '<td style="background-color:' + bgcolor.group(0)+';">' + str(val).replace(bgcolor.group(0),'') + '</td>'
                else:
                    html += '<td>' + str(val) + '</td>'
            html += '</tr>'
        html += '</table>'
        return html
    except template.VariableDoesNotExist:
        return ''


@register.filter   #@register.filter(name='charswap')
def table(value):
    "formats as table"
    try:
        header, body = listify(value)
        # ('header, body', header, body)
    except TypeError:
        return ''
    try:
        html = '<table id="simpletable"><tr>'
        if header:
            for name in header:
                if type(name) == tuple:
                    html += '<th ' + name[1] + '>' + str(name[0]) + '</th>'
                else:
                    html += '<th>' + str(name) + '</th>'
            html += '</tr>'
        for row in body:
            html += '<tr>'
            for val in row:
                if type(val) == tuple:
                    html += '<td ' + val[1] + '>' + str(val[0]).replace('<', '&lt;').replace('>', '&gt;') + '</td>'
                else:
                    html += '<td>' + str(val).replace('<', '&lt;').replace('>', '&gt;') + '</td>'
            html += '</tr>'
        html += '</table>'
        return html
    except template.VariableDoesNotExist:
        return ''
    except TypeError:
        return ''
