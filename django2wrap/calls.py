import os, pickle, re
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Call, Resource
from django.db import connection
from django.conf import settings

AGENTS = ['Boris', 'Iliyan', 'Ivelin', 'Juliana', 'Miglena', 'Niki',]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
PICKLE_PATHFILE = 'callsdata'

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class PhoneCalls:
    def __init__(self, data=[]):
        self.data = data
        
    def _parse_filename(self, filename):
        #+447879406539_2013.05.08.Wed.21.58.39.mp3
        #+000000_2013.04.10.Wed.13.52.42 .mp3
        type1 = re.match(r'(?P<contact>.+?)_(?P<year>\d\d\d\d)\.(?P<month>\d\d)\.(?P<day>\d\d)\.\w\w\w\.(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d).*?\.mp3', filename)
        #'Call Centre, 10 25 AM, Monday, 08 August 2011.mp3',
        type2 = re.match(r'(?P<contact>.+?), (?P<hour>\d\d) (?P<minute>\d\d) (?P<am>\w\w), .+?, (?P<day>\d\d) (?P<month>\w+?) (?P<year>\d\d\d\d).mp3', filename)
        if type1:
            date_details = type1.groupdict()
        if type2:
            date_details = type2.groupdict()
            date_details['month'] = MONTHS.index(date_details['month'])+1
            if date_details['am'] == 'PM':
                date_details['hour'] = (int(date_details['hour']) + 12) % 24
            del date_details['am']
        if type1 or type2:
            contact = date_details['contact']
            del date_details['contact']
            date_details = { k: int(v) for k, v in date_details.items() }
            date_details['tzinfo'] = timezone.get_default_timezone()
            time_of_call = datetime(**date_details)
        else:
            time_of_call = contact = None

        return time_of_call, contact

    def load(self, target_agent_name = None, target_time = None):
        agent_dirs = os.listdir(settings.MP3_STORAGE)
        available_data_agents = set([ z.name for z in Agent.objects.all() if z.name in agent_dirs ])
        if len(available_data_agents) == 0:
            raise MyError('No folders matching agent names in ' + settings.MP3_STORAGE)
        if target_agent_name:
            if target_agent_name in available_data_agents:
                self.data = self.load_agent(target_agent_name, target_time)
            else:
                raise MyError('No folder matching the agent name "' + target_agent_name + '" in ' + settings.MP3_STORAGE)
        else:
            for agent in available_data_agents:
                self.data += self.load_agent(agent, target_time)

    def load_agent(self, agent_folder, target_time):
        result_box = []
        for filename in os.listdir(os.path.join(settings.MP3_STORAGE, agent_folder)):
            if filename.endswith('.mp3'):
                file_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(settings.MP3_STORAGE, agent_folder, filename)))
                if (target_time and target_time < file_time) or not target_time:
                    result = self._process_file(filename, agent_folder, file_time)
                    if result: result_box.append(result)
        return result_box

    def _process_file(self, filename, agent_folder, file_time):
        result = None
        time_of_call, contact = self._parse_filename(filename)
        if not time_of_call:
            time_of_call = file_time

        shifts, day_matches = self._match_shift(time_of_call, agent_folder)
        if len(shifts) == 0: # and time_of_call < datetime(2012, 11, 26, tzinfo = timezone.get_default_timezone()):
            # print('shift not synced', filename)
            possible_agents = Agent.objects.filter(name=agent_folder).filter(start__lt=time_of_call.date()).filter(end__gt=time_of_call.date())
            if len(possible_agents) == 1:
                result = {'agent': possible_agents[0], 'shift': None, 'case': None, 'filename': filename, 'date': time_of_call}
            else:
                result = {'agent': None, 'shift': None, 'case': None, 'filename': filename, 'date': time_of_call}
                
        elif len(shifts) == 1:
            # print('exact match', filename)
            result = {'agent': shifts[0].agent, 'shift': shifts[0], 'case': None, 'filename': filename, 'date': time_of_call}

        elif len(shifts) == 2 and shifts[0].agent.id == shifts[1].agent.id:
            # print('doubleshift', filename)
            if time_of_call.hour < 15:
                the_shift = shifts.filter(tipe='Morning')[0]
            else:
                the_shift = shifts.filter(tipe='Late')[0]
            result = {'agent': the_shift.agent, 'shift': the_shift, 'case': None, 'filename': filename, 'date': time_of_call}
        else:
            for sh in shifts:
                print('file, time, agent_folder:', filename, time_of_call, agent_folder,'| daymatch', len(day_matches),':', day_matches, '| # shfts', len(shifts))
                    
        return result

    def _match_shift(self, timestamp, agent_by_foldername):
        # match_day = Shift.objects.filter(date__range=(datetime(timestamp.year, timestamp.month, timestamp.day, tzinfo = timezone.get_default_timezone()),
        #                                 datetime(timestamp.year, timestamp.month, timestamp.day, 23, 59, 59, tzinfo = timezone.get_default_timezone())))
        match_day = Shift.objects.filter(date__range=(timestamp.replace(hour=0, minute=0, tzinfo=timezone.get_default_timezone()),
                                        timestamp.replace(hour=23, minute=59, tzinfo=timezone.get_default_timezone())))
        shifts = match_day.filter(agent__name=agent_by_foldername)
        return shifts, match_day

    def save(self, destination='db'):
        if destination == 'db':
            if self.data:
                for call in self.data:
                    p = Call(**call)
                    p.save()
                return True
            else:
                return False
        elif destination == 'pickle':
            try:
                pickle.dump(self.data, open(PICKLE_PATHFILE + ".pickle", "wb" ))
                return True
            except IOError as e:
                if self.debug > 0:
                    print('Saving data to', PICKLE_PATHFILE, '.pickle failed :', e)
                return False

    def sync(self):
        # pushes to the db, only if teh record is not an exact match; used to fill up missing records, whithout touching the old ones.
        #   would fail for matching 'unique' fields -- that needs a special resolve method!
        results = []
        kwstr = lambda **kwarg: str(kwarg)
        if self.data:
            for call in self.data:
                find = Call.objects.filter(**call)
                if not find:
                    p = Call(**call)
                    p.save()
                    results.append(p.items())
            return True
        else:
            return False

    def wipe(self):
        cursor = connection.cursor()
        table_name = Call._meta.db_table
        sql = "DELETE FROM %s;" % (table_name, )
        cursor.execute(sql)

        # Call.objects.wipe_table()
        # use Call.wipe_table() instead of Call.objects.all().delete()
        # this is needed to overcome bug: https://code.djangoproject.com/ticket/16426
    
    def reload(self, *dump):
        raise MyError('You\'ll thank me later')
        self.load()
        self.wipe()
        self.save()
        resource = Resource.objects.get(name = 'calls')
        resource.last_sync = datetime.now()
        resource.save()
        return self.data

    def update(self, target_agent_name = None, target_time = None):
        self.load(target_agent_name, target_time)
        resource = Resource.objects.get(name = 'calls')
        resource.last_sync = datetime.now()
        resource.save()
        self.sync()
        return self.data

    def view(self, target_agent_name = None, target_time = None):
        def itemize(call):
            if call.agent:
                agent_name = call.agent.name
            else:
                agent_name = 'n/a'

            call_time = timezone.make_aware(call.date, timezone.get_default_timezone())
            play_button = '<a href="/listen/' + str(call.id) + '/" target="_blank">&#9658;</a>'
            return [play_button, agent_name, call_time.strftime("%d/%m/%y %H:%M"), call.case, 'contact', call.filename,] #self.shift.date]

        find = Call.objects.all()
        if target_agent_name:
            find = find.filter(agent__name = target_agent_name)
        if target_time:
            find = find.filter(date__gt = target_time)

        results = [ itemize(z) for z in find ]
        results.insert(0,['|>', 'Agent', 'Time', 'Case', 'Contact', 'File',])
        return results


    # def load_pickle_data(self):
    #     try:
    #         self.data = pickle.load(open(PICKLE_PATHFILE + ".pickle", "rb"))
    #         return True
    #     except IOError as e:
    #         if self.debug > 0:
    #             print('Loading data form', PICKLE_PATHFILE, '.pickle failed :', e)
    #         return False
