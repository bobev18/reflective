import gspread
from datetime import date, datetime, timedelta
import django.utils.timezone as timezone
import itertools, time
from django2wrap.models import Agent, Shift, Resource
from django.db import connection
from django.conf import settings

PICKLE_PATHFILE = 'shiftsdata'

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ScheduleShifts:
    def __init__(self):
        self.debug = 0
        self.data = []
        self.user = settings.GLOGIN['user']
        self.password = settings.GLOGIN['password']

    def load(self, target_year = None):
        if target_year:
            # print([(type(z),z) for z in settings.SCHEDULE_KEYS.keys()])
            self.data = self.download(**settings.SCHEDULE_KEYS[target_year])
        else:
            for year in sorted(settings.SCHEDULE_KEYS.keys()):
                new_data = []
                while len(new_data)==0:
                    print('processing year', year)
                    new_data = self.download(**settings.SCHEDULE_KEYS[year])
                    print('NEW data size', len(new_data))
                    if len(new_data) != 0:
                        # find overlapping shifts
                        new_data_datetimes = [ x['date'] for x in new_data ]
                        shifts2remove = [] # cant delete items from list that's being cycled
                        for shift in self.data:
                            if shift['date'] in new_data_datetimes:
                                shifts2remove.append(shift)
                        # do the deletions of overlapping
                        for shift in shifts2remove:
                            self.data.remove(shift)
                            print('removed duplicate shift:', shift)
                        # the overlap dates are removed from the _old_ list and will be added anew with the new_data
                        self.data += new_data
                        print('data size', len(self.data))
                    else:
                        print('failed to pull data, reprocessing in ',end='')
                        for i in range(5,0,-1):
                            print(i,'..',end='')
                            time.sleep(1)

    def download(self, key, datarange, init_date = None, map_meaningful = None):
        # print('key', key)
        gc = gspread.login(self.user, self.password)
        if isinstance(init_date, date):
            pass
        elif isinstance(init_date, dict):
            init_date = datetime(tzinfo = timezone.get_default_timezone(), **init_date).date()
        elif isinstance(init_date, str):
            init_date = date.strptime(init_date, "%d %b %y") # 26 nov 12
        else:
            init_date = self._get_init_date(gc, key)

        def datasize(drange):
            start, end = drange.split(':')
            letters = lambda x, boo: ''.join([ z for z in x if z.isdigit()!=boo ])
            start_letters = letters(start,1)
            start_digits = letters(start,0)
            end_letters = letters(end,1)
            end_digits = letters(end,0)
            col_names = list(map(str.strip,map(''.join,itertools.combinations_with_replacement(' ABCDEFGHIJKLMNOPQRSTUVWXYZ', 2))))[1:]
            x_size = col_names.index(end_letters) - col_names.index(start_letters)
            y_size = int(end_digits) - int(start_digits)
            return x_size + 1, y_size + 1 # +1 because bothe start and end index are part of the range

        # wks = gc.open("schedule").get_worksheet(1)
        wks = gc.open_by_key(key).get_worksheet(1)
        sheet_data = wks.range(datarange)
        # print('sheet data', sheet_data)
        results = self._parse_shifts(init_date, sheet_data, *datasize(datarange), map_meaningful=map_meaningful)

        return results

    def view_odities(self, data=None):
        if not data:
            data = self.data
        
        group_by_date = {}
        for shift in self.data:
            if shift.date.date() in group_by_date.keys():
                group_by_date[shift.date.date()].append(shift)
            else:
                group_by_date[shift.date.date()] = [shift]

        # detect odities
        results = []
        for date in group_by_date.keys():
            if len(group_by_date[date]) < 2 or len(group_by_date[date]) > 3:
                print(date, group_by_date[date])
                results.append([date, group_by_date[date]])

        return results

    def save(self):
        if self.data:
            for row in self.data:
                p = Shift(**row)
                p.save()
            return True
        else:
            return False

    def sync(self):
        # pushes to the db, only if teh record is not an exact match; used to fill up missing records, whithout touching the old ones.
        #   would fail for matching 'unique' fields -- that needs a special resolve method!
        results = []
        # kwstr = lambda **kwarg: str(kwarg)
        if self.data:
            for shift in self.data:
                # find = Shift.objects.filter(**shift)
                find = Shift.objects.filter(date=shift['date'])
                if not find:
                    p = Shift(**shift)
                    p.save()
                    results.append(p.items())
            return True
        else:
            return False

    def wipe(self):
        cursor = connection.cursor()
        table_name = Shift._meta.db_table
        sql = "DELETE FROM %s;" % table_name
        cursor.execute(sql)

    def reload(self, *dump):
        raise MyError('You\'ll thank me later')
        self.load()
        self.wipe()
        self.save()
        resource = Resource.objects.get(name = 'shifts')
        resource.last_sync = datetime.now(timezone.get_default_timezone())
        resource.save()
        return self.data

    def update(self, target_agent_name = None, target_time = None):
        self.load(max(settings.SCHEDULE_KEYS.keys())) # or could be 9999
        resource = Resource.objects.get(name = 'shifts')
        resource.last_sync = datetime.now(timezone.get_default_timezone())
        resource.save()
        self.sync()
        return self.data

    def view(self, target_agent_name = None, target_time = None):
        # self.view_odities()
        # print('input', target_agent_name, target_time)
        tz = timezone.get_current_timezone()
        def strdate(shift):
            return timezone.make_naive(shift.date, tz).strftime("%y/%m/%d")
            # return {'date': timezone.make_naive(shift.date, tz).strftime("%d/%m/%y"), 'data': (shift.agent.name[:2], shift.tipe, shift.color)}

        self.data = find = Shift.objects.order_by('date')
        if target_agent_name:
            find = find.filter(agent__name = target_agent_name)
        if target_time:
            find = find.filter(date__gt = target_time)

        first_find_date = find[0].date.date() # should be the smallest because of the order
        shiftz = {'Morning': 0, 'Middle': 1, 'Late' : 2}
        dates = {}
        for shift in find:
            if shift.date.date() in dates.keys():
                dates[shift.date.date()][shiftz[shift.tipe]] = (shift.agent.name[:2], shift.color)
            else:
                dates[shift.date.date()] = {shiftz[shift.tipe]: (shift.agent.name[:2], shift.color)}

        for back_index in range(7):
            # print('starter_date', starter_date, starter_date.weekday())
            if min(dates.keys()).weekday() != 0: 
                dates[min(dates.keys()) + timedelta(days=-1)] = {0: ('', '#999999')}
                # print('added', min(dates.keys()), dates[min(dates.keys())])
            else:
                break
        results = []
        big_line = sorted(dates.keys())
        for section_index in range(0,len(big_line),28):
            # adding row for the entire section
            row_mo = []
            row_d = []
            row_s = [[], [], []]
            row_morning = []
            row_mid = []
            row_late = []

            # if day of section_index + 0 != Monday: #0 being the day index
            #     insert _fake_day_ to rows1..4 at position 0
            # for back_index in range(7):
            #     if (first_find_date + timedelta(days=-back_index)).day_of_week() != 0: 
            #         row.insert(0,('','#999999'))
            #         row_morning.insert(0,('','#999999'))
            #         row_mid.insert(0,('','#999999'))
            #         row_late.insert(0,('','#999999'))
            #     else:
            #         break
                
            for day_index in range(28):
                try:
                    # print(section_index,day_index,section_index+day_index)
                    # print(big_line[section_index+day_index],dates[big_line[section_index+day_index]],dates[big_line[section_index+day_index]].keys())
                    row_mo.append(big_line[section_index+day_index].strftime('%b'))
                    row_d.append(big_line[section_index+day_index].strftime('%d%a')[:3])
                    for shi in range(len(row_s)):
                        if shi in dates[big_line[section_index+day_index]].keys():
                            content = dates[big_line[section_index+day_index]][shi]
                            row_s[shi].append(content[0]+content[1])
                        else:
                            row_s[shi].append('')

                        
                    # row_morning.append(dates[big_line[section_index+day_index]][0][0])
                    # if 1 in dates[big_line[section_index+day_index]].keys():
                    #     row_mid.append(dates[big_line[section_index+day_index]][1][0])
                    # else:
                    #     # row_mid.append(('','#ffffff'))
                    #     row_mid.append('')
                    # if 2 in dates[big_line[section_index+day_index]].keys():
                    #     row_late.append(dates[big_line[section_index+day_index]][2][0])
                    # else:
                    #     # row_late.append(('','#ffffff'))
                    #     row_late.append('')
                except:
                    pass
            results.append([big_line[section_index].year])
            results.append(row_mo)
            results.append(row_d)
            for shi in range(len(row_s)):
                results.append(row_s[shi])
                
            # results.append(row_morning)
            # results.append(row_mid)
            # results.append(row_late)

        # results = self.view_odities() ## !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        return results

    def simple_view(sefl,  target_agent_name = None, target_time = None):
        # print('input', target_agent_name, target_time)
        tz = timezone.get_current_timezone()
        def itemize(shift):
            return [shift.agent.name, timezone.make_naive(shift.date, tz).strftime("%d/%m/%y %H:%M"), shift.tipe,] # shift.color]

        find = Shift.objects.order_by('date')
        if target_agent_name:
            find = find.filter(agent__name = target_agent_name)
        if target_time:
            find = find.filter(date__gt = target_time)


        results = [ itemize(z) for z in find ]
        results.insert(0, ['Agent Name', 'Shift Start Time', 'Shift Type',]) # 'Color Code'])
        return results

    def _get_init_date(self, conn_obj, key, init_year = '12'):
        # Return the starting date for the document
        # We have few hardcodded items, but that's OK for now:
        #   working with 1st sheet of the spreadsheet document:
        # wks = conn_obj.open("schedule").get_worksheet(0)
        wks = conn_obj.open_by_key(key).get_worksheet(0)

        #   working with the specific range where the date should be by convetion
        init_date_range = wks.range('B1:B2')
        #   year is hardcoded -- could be derived from "current" year, but that's not urgent
        return datetime.strptime(init_date_range[0].value + ' ' + init_date_range[1].value + ' ' + init_year, "%d %b %y",
                tzinfo = timezone.get_default_timezone())

    def _parse_shifts(self, init_date, sheet_data, columns_count = 28, rows_count = 119, map_meaningful = [0,0,0,1,2,3,0,0]):
        rows = []
        mylower = lambda x: x.lower() if isinstance(x, str) else ''
        for i in range(0, len(sheet_data), columns_count): # 28 days per row
            sub = sheet_data[i:i+columns_count]
            rows.append([mylower(z.value) for z in sub])
            # print(i, rows[-1])

        # sheet_data is one big chain, but we need to split into rows, so we can filter the meaningful ones
        #   once the filtration is through, we join the data to one big chain
        meaningful = itertools.cycle(map_meaningful)
        shifts_types = [('Morning', 7), ('Middle', 10), ('Late', 14)]
        biglist = []
        section_index = -1
        for row in rows:
            meaning = next(meaningful)
            if meaning:
                # print('row', row)
                shift_type = shifts_types[meaning-1]
                if shift_type[0] == 'Morning':
                    section_index += 1
                section_date = init_date + timedelta(days=section_index*columns_count)
                for i in range(len(row)):
                    loop_date = section_date + timedelta(days=i)
                    shift_time = datetime(loop_date.year, loop_date.month, loop_date.day, shift_type[1],
                                tzinfo = timezone.get_default_timezone())
                    agent = self.adjusted(row[i], loop_date)
                    if agent:
                        biglist.append({'color': row[i], 'tipe': shift_type[0], 'date': shift_time, 'agent': agent})

        return biglist

    def adjusted(self, color, date):
        # print(type(date),date)
        colored_agent = Agent.objects.filter(current_color=color)
        # print('colored_agent', colored_agent)
        if len(colored_agent) > 0:
            for agent in colored_agent:
                # print('if date >= agent.start and date < agent.end', date, agent.start, agent.end)
                if date >= agent.start and date < agent.end:
                    return agent
  
    def clear_db_duplocates(self):
        from django.db import connection
        cursor = connection.cursor()
        q = """delete   from django2wrap_shift
            where id not in
            (
                select  min(id)
                from    django2wrap_shift
                group by
                    date,
                    color,
                    tipe,
                    agent_id
            )"""
        cursor.execute(q)