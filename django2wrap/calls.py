import os, pickle, re
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Call

agents = ['Boris', 'Iliyan', 'Ivelin', 'Juliana', 'Miglena', 'Niki',]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
PICKLE_PATHFILE = 'callsdata'

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Calls:
    def __init__(self, data=[]):
        self.data = data
        
    def load(self):
        box = []
        dropouts = []
        for agent in agents:
            for dirname, dirnames, filenames in os.walk('Z:\\' + agent):
                for filename in filenames:
                    full_path = os.path.join(dirname, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                    #+447879406539_2013.05.08.Wed.21.58.39.mp3
                    #+000000_2013.04.10.Wed.13.52.42 .mp3
                    type1 = re.match(r'.+?_(?P<year>\d\d\d\d)\.(?P<month>\d\d)\.(?P<day>\d\d)\.\w\w\w\.(?P<hour>\d\d)\.(?P<minute>\d\d)\.(?P<second>\d\d).*?\.mp3', filename)
                    #'Call Centre, 10 25 AM, Monday, 08 August 2011.mp3',
                    type2 = re.match(r'.+?, (?P<hour>\d\d) (?P<minute>\d\d) (?P<am>\w\w), .+?, (?P<day>\d\d) (?P<month>\w+?) (?P<year>\d\d\d\d).mp3', filename)
                    if type1:
                        date_details = type1.groupdict()
                    elif type2:
                        date_details = type2.groupdict()
                        date_details['month'] = MONTHS.index(date_details['month'])+1
                        if date_details['am'] == 'PM':
                            date_details['hour'] = (int(date_details['hour']) + 12) % 24
                        del date_details['am']
                    else:
                        if filename.count('.mp3') == 0:
                            continue # file not mp3 --> next item in the file loop
                        else:
                            pass #non standard name format --> use "last modified" filetime
                    if type1 or type2:
                        date_details = { k: int(v) for k, v in date_details.items() }
                        date_details['tzinfo'] = timezone.get_default_timezone()
                        time_of_call = datetime(**date_details)
                    else:
                        time_of_call = file_time

                    shifts, day_matches = self.match_shift(time_of_call, agent)
                    if len(shifts) == 0 and time_of_call < datetime(2012, 11, 26, tzinfo = timezone.get_default_timezone()): # shit not synced
                        # print('lacking shift reference, but added', filename)
                        possible_agents = Agent.objects.filter(name=agent).filter(start__lt=time_of_call.date()).filter(end__gt=time_of_call.date())
                        if len(possible_agents) == 1:
                            box.append({'agent': possible_agents[0], 'shift': None, 'case': None, 'filename': filename, 'date': time_of_call})
                        else:
                            print('daymatch', len(day_matches), 'shftz returned', len(shifts), '|| fn,ft,ct,ag,day_matches::', filename, file_time, time_of_call, agent, day_matches,'||\nagents', Agent.objects.filter(name=agent))
                            
                    elif len(shifts) == 1: # all fine
                        # print('inserted one for', filename)
                        box.append({'agent': shifts[0].agent, 'shift': shifts[0], 'case': None, 'filename': filename, 'date': time_of_call})
                    elif len(shifts) == 2 and shifts[0].agent.id == shifts[1].agent.id: #doubleshift
                        if time_of_call.hour < 15:
                            target_shift_tipe = 'Morning'
                        else:
                            target_shift_tipe = 'Late'
                        the_shift = shifts.filter(tipe=target_shift_tipe)[0]
                        # print('doubleshift -> resolved for', filename)
                        box.append({'agent': the_shift.agent, 'shift': the_shift, 'case': None, 'filename': filename, 'date': time_of_call})
                    else: #mystery
                        for sh in shifts:
                            print('daymatch', len(day_matches), 'shftz returned', len(shifts), '|| fn,ft,ct,ag,day_matches::', filename, file_time, time_of_call, agent, day_matches)
                    
        self.data = box

    def match_shift(self, timestamp, agent_by_foldername):
        match_day = Shift.objects.filter(date__range=(datetime(timestamp.year, timestamp.month, timestamp.day,tzinfo = timezone.get_default_timezone()),
                                        datetime(timestamp.year, timestamp.month, timestamp.day, 23, 59, 59,tzinfo = timezone.get_default_timezone())))
        shifts = match_day.filter(agent__name=agent_by_foldername)
        return shifts, match_day

    def save_db_data(self):
        if self.data:
            for call in self.data:
                p = Call(**call)
                p.save()
            return True
        else:
            return False

    def wipe_db(self):
        Call.objects.all().delete()

    def load_pickle_data(self):
        try:
            self.data = pickle.load(open(PICKLE_PATHFILE + ".pickle", "rb"))
            return True
        except IOError as e:
            if self.debug > 0:
                print('Loading data form', PICKLE_PATHFILE, '.pickle failed :', e)
            return False

    def save_pickle_data(self):
        try:
            pickle.dump(self.data, open(PICKLE_PATHFILE + ".pickle", "wb" ))
            return True
        except IOError as e:
            if self.debug > 0:
                print('Saving data to', PICKLE_PATHFILE, '.pickle failed :', e)
            return False