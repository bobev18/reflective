import os
from datetime import datetime, timedelta
import django.utils.timezone as timezone
from django2wrap.models import Agent, Shift, Call

agents = ['Boris', 'Iliyan', 'Ivelin', 'Juliana', 'Miglena', 'Niki',]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
class Calls:
    def __init__(self, data=[]):
        self.data = data
        
    def load(self):
        box = []
        for agent in agents:
            for dirname, dirnames, filenames in os.walk('Z:\\' + agent):
                for filename in filenames:
                    full_path = os.path.join(dirname, filename)
                    if filename.count('.mp3') > 0:
                        try:
                            if filename.count('_') > 0:
                                #+447879406539_2013.05.08.Wed.21.58.39.mp3
                                fndate = filename.split('_')[-1] 
                                fndate = [ int(z) for z in fndate.split('.') if z.isdigit() ]
                                # time_of_call = datetime(*fndate)
                            else:
                                #'Call Centre, 10 25 AM, Monday, 08 August 2011.mp3',
                                fndate = filename.split('.')[0] #clear .mp3
                                fndate = min([ fndate.replace(MONTHS[z],str(z+1)) for z in range(len(MONTHS)) ], key=len)
                                fndate = fndate.split(',')[1:] #clear <name/location>
                                # fndate = fndate[2] + fndate[0]
                                fndate = [ int(z) for z in fndate[2].split(' ') if z.isdigit() ][::-1] + [ int(z) for z in fndate[0].split(' ') if z.isdigit() ]
                                # fndate = [ int(z) for z in fndate.split(' ') if z.isdigit() ]
                                # print(fndate)
                            time_of_call = datetime(*fndate)
                        except IndexError as e:
                            print('IndexError:', e, 'fn:', filename) 
                            time_of_call = datetime.fromtimestamp(os.path.getmtime(full_path))
                        aware_time_of_call = timezone.make_aware(time_of_call, timezone.get_current_timezone())
                        shifts = Shift.objects.exclude(date__gt=time_of_call).filter(date__gt=time_of_call + timedelta(hours=-8))
                        if len(shifts)==0:
                            print('meh', len(shifts), shifts, full_path, time_of_call, aware_time_of_call)

                        for sh in shifts:
                            # box.append({'agent': sh.agent.id, 'shift': sh.id, 'case': None, 'filename': filename, 'date': time_of_call})
                            box.append({'agent': sh.agent, 'shift': sh, 'case': None, 'filename': filename, 'date': time_of_call})
                    
        self.data = box

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