import gspread
from datetime import date, datetime, timedelta
import pickle
from django2wrap.models import Agent, Shift

# NAME_ENCODE = {'Juliana': '#ff0000', 'Boris': '#0000ff', 'Ivo': '#ffff00', 'Megi': '#00ff00'}
NAME_DECODE = {'#ff0000': 'Juliana', '#0000ff': 'Boris', '#ffff00': 'Iliyan', '#00ff00': 'Megi'}
PICKLE_PATHFILE = 'shiftsdata'

AGENT_PERIODS = {
    '#ff0000': [{'start': datetime(2010, 4, 1), 'end': datetime(2020, 1, 1), 'name': 'Juliana'}], #
    '#ffff00': [
        {'name': 'Iliyan', 'start': datetime(2010, 3, 1),   'end': datetime(2013, 3, 1)},#
        {'name': 'Niki',   'start': datetime(2013, 3, 1),   'end': datetime(2013, 7, 1)}, #
        {'name': 'Boris',  'start': datetime(2013, 7, 1),   'end': datetime(2013, 10, 12)}, #
        {'name': 'Radi',    'start': datetime(2013, 10, 13), 'end': datetime(2020, 1, 1)},
    ],
    '#00ff00': [
        {'name': 'Megi',   'start': datetime(2010, 4, 1),   'end': datetime(2011, 1, 16)}, #
        {'name': 'Boris',  'start': datetime(2011, 3, 1),   'end': datetime(2011, 3, 20)}, #
        {'name': 'Niki',   'start': datetime(2011, 3, 21),  'end': datetime(2011, 12, 31)}, #
        {'name': 'Megi',   'start': datetime(2012, 1, 1),   'end': datetime(2013, 9, 20)}, #
        {'name': 'Rosti',  'start': datetime(2013, 10, 13), 'end': datetime(2020, 1, 1)},
    ],
    '#0000ff': [
        {'name': 'Boris1', 'start': datetime(2010, 4, 1),   'end': datetime(2010, 11, 12)}, #
        {'name': 'Niki',   'start': datetime(2010, 11, 22), 'end': datetime(2011, 3, 20)}, #
        {'name': 'Boris',  'start': datetime(2011, 3, 21),  'end': datetime(2013, 6, 30)}, #
        {'name': 'Ivo',   'start': datetime(2013, 7, 1),   'end': datetime(2020, 1, 1)},
    ]
}

class Shifts:
    def __init__(self, data=[]):
        self.debug = 0
        self.raw = []
        self.data = data
        self.init_date = date(2012, 11, 26)

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

    def save_db_data(self):
        if self.data:
            for row in self.data:
                p = Shift(**row)
                p.save()
            return True
        else:
            return False

    def wipe_db(self):
        Shift.objects.all().delete()

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

    def set_init_date(self, conn_obj, init_year = '12'):
        # Return the starting date for the document
        # We have few hardcodded items, but that's OK for now:
        #   working with 1st sheet of the spreadsheet document:
        wks = conn_obj.open("schedule").get_worksheet(0)
        #   working with the specific range where the date should be by convetion
        init_date_range = wks.range('B1:B2')
        #   year is hardcoded -- could be derived from "current" year, but that's not urgent
        self.init_date =  datetime.strptime(init_date_range[0].value + ' ' + init_date_range[1].value + ' ' + init_year, "%d %b %y", )

    def download_data(self, user, password):
        # returns list of tuple of the names for the agent that worked on morning, middle and late shifts

        # # Login with your Google account
        gc = gspread.login(user, password)
        #determine initial date
        self.set_init_date(gc)
        # # Open a worksheet from spreadsheet with one shot
        #  working with second sheet by convention
        wks = gc.open("schedule").get_worksheet(1)
        #  working with specific range by convention
        sheet = wks.range('B1:AC120')
        # print(len(sheet))
        subs = []
        for i in range(0, len(sheet), 28): # 28 days per row
            sub = sheet[i:i+28]
            mylower = lambda x: x.lower() if isinstance(x, str) else ''
            subs.append([mylower(z.value) for z in sub])

        subs = subs[3:] # removes the first 3 rows - that are header dates
        biglist = []
        #  8 = assuming 3 rows for denoting date, 3 rows for shifts and 2 notation/spacing rows
        for i in range(0, len(subs), 8):
            for day in range(len(subs[i])):
                biglist.append((subs[i][day],subs[i+1][day],subs[i+2][day],))

        self.raw = biglist

        box = []
        for i in range(len(biglist)):
            day = biglist[i]
            aware_date = timezone.make_aware(self.init_date, timezone.get_default_timezone())
            loop_date = aware_date + timedelta(days=i)
            # print(type(loop_date), loop_date,'|',type(loop_date.date()), loop_date.date())
            tipes = [('Morning', 7), ('Middle', 10), ('Late', 14)]
            
            for j in range(3):
                record = {}
                record['date'] = loop_date + timedelta(hours=tipes[j][1])
                record['color'] = day[j]
                record['tipe'] = tipes[j][0]
                agent = self.adjusted(day[j], loop_date.date())
                if agent:
                    record['agent_id'] = agent.id
                    # print('color, agent:', record['color'], agent.id, agent)
                    box.append(record)

        #debug
        # for i in range(0,len(box),28):
        #     print(box[i:i+28])
        #     print()  
        self.data = box

    def adjusted(self, color, date):
        # print(type(date),date)
        colored_agent = Agent.objects.filter(current_color=color)
        # print('colored_agent', colored_agent)
        if len(colored_agent) > 0:
            for agent in colored_agent:
                # print('if date >= agent.start and date < agent.end', date, agent.start, agent.end)
                if date >= agent.start and date < agent.end:
                    return agent
    
    def old_adjusted(self, color, date):
        if color in AGENT_PERIODS.keys():
            for period in AGENT_PERIODS[color]:
                if date >= period['start'] and date < period['end']:
                    return period['name']
        return ''
       
    def day2shifts(self, date):
        delta = date - self.init_date
        return self.data[delta.days]

    # def adjusted_old(self, name, date):
    #     result = name
    #     if name == 'Iliyan': #yellow
    #         if  date < datetime(2013, 3, 1):
    #             pass
    #         elif  date >= datetime(2013, 3, 1) and date < datetime(2013, 6, 1):
    #             result = 'Niki'
    #         elif date >= datetime(2013, 6, 1) and date < datetime(2013, 10, 14): 
    #             result = 'Boris'
    #         elif date >= datetime(2013, 10, 14): 
    #             result = 'Radi'
    #         else:
    #             pass
    #     elif name == 'Boris': #blue
    #         if  date < datetime(2013, 6, 1):
    #             pass
    #         else: 
    #             result = 'Ivo'
    #     elif name == 'Megi':
    #         if  date < datetime(2013, 9, 20):
    #             pass
    #         else: 
    #             result = 'Rosti'
    #     else:
    #         pass
    #     return result
            

# print(adjusted('Iliyan', datetime(2013, 2, 20)))
# print(adjusted('Iliyan', datetime(2013, 9, 20)))
# print(adjusted('Iliyan', datetime(2013, 11, 20)))

# dayz = [datetime(2013, 2, 25), datetime(2013, 7, 30), datetime(2013, 10, 30)]
# sched = shifts()
# #load 
# if not sched.load_pickle_data(): #attempts load from picke
#     sched.download_data()
#     sched.save_pickle_data()
# for d in dayz:
#     print(d, sched.day2shifts(d))
