import gspread
from datetime import date, datetime, timedelta
import pickle, itertools
from django2wrap.models import Agent, Shift

PICKLE_PATHFILE = 'shiftsdata'

class Shifts:
    def __init__(self, data=[]):
        self.debug = 0
        self.raw = []
        self.data = data
        self.init_date = date(2012, 11, 26, tzinfo = timezone.get_default_timezone())
        self.key = "0AuV8A4Kd_KBydFhYOVRVQk45LVRDSmpJLVEtZUZBUHc&hl"

   
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

    def set_init_date(self, conn_obj, key, init_year = '12'):
        # Return the starting date for the document
        # We have few hardcodded items, but that's OK for now:
        #   working with 1st sheet of the spreadsheet document:
        # wks = conn_obj.open("schedule").get_worksheet(0)
        wks = conn_obj.open_by_key(key).get_worksheet(0)

        #   working with the specific range where the date should be by convetion
        init_date_range = wks.range('B1:B2')
        #   year is hardcoded -- could be derived from "current" year, but that's not urgent
        self.init_date = datetime.strptime(init_date_range[0].value + ' ' + init_date_range[1].value + ' ' + init_year, "%d %b %y", )
        
    def download_data(self, user, password, key = None, datarange = 'B1:AC120'):
        def datasize(drange):
            start, end = drange.split(':')
            letters = lambda x, boo: ''.join([ z for z in x if z.isdigit()!=boo ])
            start_letters = letters(s,1)
            start_digits = letters(s,0)
            end_letters = letters(e,1)
            end_digits = letters(e,0)
            col_names = list(map(str.strip,map(''.join,itertools.combinations_with_replacement(' ABCDEFGHIJKLMNOPQRSTUVWXYZ', 2))))
            x_size = col_names.index(end_letters) - col_names.index(start_letters)
            y_size = int(end_digits) - int(start_digits)
            return x_size, y_size

        gc = gspread.login(user, password)
        if not key:
            key = self.key
        self.set_init_date(gc, key)
        # wks = gc.open("schedule").get_worksheet(1)
        wks = gc.open_by_key(key).get_worksheet(1)
        sheet_data = wks.range(datarange)
        results = self._parse_shifts(sheet_data, *datasize(datarange))
        return results

    def _parse_shifts(self, sheet_data, columns_count = 28, rows_count = 119, map_meaningful = [0,0,0,1,1,1,0,0]):
        rows = []
        mylower = lambda x: x.lower() if isinstance(x, str) else ''
        for i in range(0, len(sheet_data), columns_count): # 28 days per row
            sub = sheet_data[i:i+columns_count]
            rows.append([mylower(z.value) for z in sub])

        # sheet_data is one big chain, but we need to split into rows, so we can filter the meaningful ones
        #   once the filtration is through, we join the data to one big chain
        meaningful = itertools.cycle(map_meaningful)


        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
         subs = subs[3:] # removes the first 3 rows - that are header dates
        biglist = []
        #  8 = assuming 3 rows for denoting date, 3 rows for shifts and 2 notation/spacing rows
        for i in range(0, len(subs), 8):
            for day in range(len(subs[i])):
                biglist.append((subs[i][day],subs[i+1][day],subs[i+2][day],))
        self.raw = biglist

        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # the snippet above, does not only filter the meaningfult rows, but, also fills in a chain, with tuples containing to 3 shifts each



        # process      
        shifts_types = itertools.cycle([('Morning', 7), ('Middle', 10), ('Late', 14)])
        box = []
        for i in range(len(biglist)): # cycle rows
            day = biglist[i]
            # aware_date = timezone.make_aware(self.init_date, timezone.get_default_timezone())
            aware_date = self.init_date
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







        bigchain = itertools.chain(*meaningful)
        # >>> x = [[33,33,33], [1,56,34,0,-2,1], [10,67,67,67]]
        # >>> list(itertools.chain(*x))
        # [33, 33, 33, 1, 56, 34, 0, -2, 1, 10, 67, 67, 67]
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
    
    # def old_adjusted(self, color, date):
    #     if color in AGENT_PERIODS.keys():
    #         for period in AGENT_PERIODS[color]:
    #             if date >= period['start'] and date < period['end']:
    #                 return period['name']
    #     return ''
       
    # def day2shifts(self, date):
    #     delta = date - self.init_date
    #     return self.data[delta.days]

    # def load_pickle_data(self):
    #     try:
    #         self.data = pickle.load(open(PICKLE_PATHFILE + ".pickle", "rb"))
    #         return True
    #     except IOError as e:
    #         if self.debug > 0:
    #             print('Loading data form', PICKLE_PATHFILE, '.pickle failed :', e)
    #         return False

    # def save_pickle_data(self):
    #     try:
    #         pickle.dump(self.data, open(PICKLE_PATHFILE + ".pickle", "wb" ))
    #         return True
    #     except IOError as e:
    #         if self.debug > 0:
    #             print('Saving data to', PICKLE_PATHFILE, '.pickle failed :', e)
    #         return False
            

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
