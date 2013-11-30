from sys import stdout
from datetime import datetime, timedelta
from datetime import time as dtime
# import django.utils.timezone as timezone

def clear_bad_chars(text):
    # KILL BAD UNICODE
    BAD_CHARS = ['\u200b', '\u2122', '™', '\uf04a', '\u2019', '\u2013', '\u2018', '\xae', '\u201d',  ]
    BAD_CHARS = ['\u200b', '\u2122', '™', '\uf04a', '\u2019', '\u2013', '\u2018', '\xae', '\u201d', '©', '“' ]
    for bc in BAD_CHARS:
        text = text.replace(bc, '')
    # text = text.encode('utf-8','backslashreplace').decode('utf-8','surrogateescape') # failing
    # I think I need to have the encoding specified during the urllib2.read( ) === myweb3
    # REGULAR CLEANS
    text = text.replace('u003C', '<')
    text = text.replace('u003E', '>')
    return text
    # ok - tied the following and it errored on char: '\\u200b'
    # return smart_text(text, encoding='utf-8', strings_only=False, errors='strict')

def safe_print(*args, sep=' ', end='\n' ):
    sep = sep.encode('utf8')
    end = end.encode('utf8')
    for arg in args:
        val = str(arg).encode('utf8')
        stdout.buffer.write(val)
        stdout.buffer.write(sep)
    stdout.buffer.write(end)

def siphon(text, begin, end):
    m = re.search(begin + r'(.+?)' + end, text, re.DOTALL)
    if m:
        return m.group(1)
    else:
        return ''

SHIFT_TIMES = {'start': 5, 'end': 20, 'workhours': 15, 'non workhours': 9}

def worktime_diffference(start, end, debug = None):
    # workout the overlap between the argument period and the support working hours
    if debug:
        print('Start of period: ', start.strftime('%d/%m/%Y %H:%M'))
        print('End of period  : ', end.strftime('%d/%m/%Y %H:%M'))
        print('awareness', start.tzinfo, end.tzinfo)
    day = timedelta(days=1)
    hour = timedelta(hours=1)
    if start.time() < dtime(SHIFT_TIMES['start']):
        start = start.replace(hour=SHIFT_TIMES['start']).replace(minute=0)
    print(start.time(), dtime(SHIFT_TIMES['end']), start.time() > dtime(SHIFT_TIMES['end']))
    if start.time() > dtime(SHIFT_TIMES['end']):
        start = start.replace(hour=SHIFT_TIMES['start']).replace(minute=0) + timedelta(days=1)
    if end.time() < dtime(SHIFT_TIMES['start']):
        end = end.replace(hour=SHIFT_TIMES['end']).replace(minute=0) + timedelta(days=-1)
    if end.time() > dtime(SHIFT_TIMES['end']):
        end = end.replace(hour=SHIFT_TIMES['end']).replace(minute=0)
    if debug: print('adjusted times:', start, end)
    if start.date() != end.date():
        delta_days = (end - start) // day # delta days (17 // 3 = 2)
        transposed_end = end - timedelta(days=delta_days)
        result = transposed_end - start + delta_days * timedelta(hours = SHIFT_TIMES['workhours']) #
        if debug:
            print('delta days:', str(delta_days))
            print('transposed end: ', transposed_end.strftime('%d/%m/%Y %H:%M'))
        if transposed_end.date() != start.date():
            result += timedelta(hours=-SHIFT_TIMES['non workhours'])
        if debug:
            print('transposed end', transposed_end, 'start', start, 'result:', result)
    else:
        result = end - start
        if debug:
            print('end', end, 'start', start, 'result:', result)
    return round(result / hour, 2)

LINKS = {
    'WLK': '<a href="https://eu1.salesforce.com/%s" target="_blank">%s</a>',
    'RSL': '<a href="https://emea.salesforce.com/%s" target="_blank">%s</a>',
}

def case_to_num_link(case):
    num, sfdc, link = [ getattr(case, z) for z in ['number', 'sfdc', 'link'] ]
    return LINKS[sfdc] % (link, num)