# coding: utf-8

######################
## Daily Chaser Bot for ST&WLK  --  copy of version 0.74 --
##
## version 0.72
## ~ count of open cases
## ~ count of cases that need chasing
## ~ table of cases that need chasing
## ~ count of cases that are postponed
## ~ results saved in HTML export
## ~ results sent over email
## ~ the HTML export has extra table with postponed case details
## ~ postpone ignored if there is subsequent client comment
##
## TODO:
## ~ postpone reason - key by "postpone reason:.{0,1}[a-zA-Z ]{12,}" (except that this will be broken by punctuation :( [is tehre RegEx for evaluating text?])
## ~ "depostpone"
## ~ make all subsequent comments revoke postpone
## ~ make postpone count the newest postpone, not the longest.
##
## ? refactoring to introduce more OOP ??
## -

import time, re, pickle, datetime, os, sys
import os.path, time
import django2wrap.settings

####### the code below was used to allow myweb2 without including it in the project
from .bicrypt import BiCrypt
import urllib.request

# with open("C:/gits/django2wrap/django2wrap/local_settings.py", 'rt') as f:
# 	module_file = f.read()
# matches = re.findall(r"MODULEPASS = '(.+?)'", module_file)
codder = BiCrypt(django2wrap.settings.MODULEPASS)  #matches[0])
response = urllib.request.urlopen('http://eigri.com/myweb2.encoded')
code = response.read()      # a `bytes` object
decoded_msg = codder.decode(code)
exec(decoded_msg)

## ..................................................................................... ##
TOADDRS  = ['iliyan@reflectivebg.com','support@reflective.com','itsupport@wightlink.co.uk']
## ..................................................................................... ##
FROMADDR = 'wiki@reflectivebg.com'
## ..................................................................................... ##
LOGIN    = FROMADDR
## ..................................................................................... ##
PASSWORD = "stresstesterwiki"
## ..................................................................................... ##
# LAST_REUSLTS = 'c:/gits/django2wrap/django2wrap/templates/last_chase_ruslts.html'
LAST_REUSLTS = os.path.join(django2wrap.settings.TEMPLATE_DIRS[0], 'last_chase_ruslts.html')

###########################################################################################

def main_chase():

    ###########################################################################################
    ## *********************************** CONFIGURATION *********************************** ##
    num_records_to_pull = '300'
    ## ..................................................................................... ##
    pages_back = 1
    ## ..................................................................................... ##
    fdir = 'd:/temp/'
    ## ..................................................................................... ##
    pickledir = ''
    ## ..................................................................................... ##
    outsladetails = 0
    ## ..................................................................................... ##
    debug = -1
    ## ..................................................................................... ##
    myweb_module_debug = -1

    def remove_html_tags(data):
        p = re.compile(r'<.*?>')
        return p.sub('', data)

    def casetimes(zodate,dump,zlink):                              # parses the hsitory table to calculate the time the case was with support
        #                                               # support pending is defined by state ('New')('In Progress')
        #                                              # casetimeS as difference from casetime returns the initial responce period (new->responded)
        #import re, time
        verbose = 0
        if verbose >1:debugit(50*'*')
        if verbose >0:debugit("zodate catched in dump as " + zodate)

        def remove_html_tags(data):
            p = re.compile(r'<.*?>')
            return p.sub('', data)

        tmp = parse(dump,'Case Number','Case Owner')
        zid = remove_html_tags(tmp).strip('\n')

        #*************** testing
        #if htbl.count('Tom Fraser')>0: ## used to be a bit further down
        if zid in ['00001802','00004706','00004707']:
            verbose = 2
        #***********************

        if verbose > 0:
            debugit('*'*20,zid,'*'*20)

        if dump.count('Created.')==0:
            debugit("Error -- no 'Created.' found in the returned HTML !!!!!!!!!!!!!!! (should extend above ?rowsperlist=100)")
            debugit(zlink)

        #zodate = parse(dump,'Date/Time Opened</td><td class="dataCol col02">','</td><td class="labelCol">Case Origin')

        htbl = parse(dump, 'Case History</h3>','class="backToTop"')
        htbl = parse(htbl, '<!-- ListRow -->','</table>')
        #debugit htbl

        # we have Date  User    Action
        htbox = htbl.split('<!-- ListRow -->')
        #for i in range(len(htbox)-1,-1,-1):
        #    htdet  = htbox[i]

        timebox = []
        lastrowdate = ''
        for htdet in htbox: # cycles rows in the history table
            hisdet = str(htdet).strip()
            hisdet = hisdet.replace('<th','<td')
            hisdet = hisdet.replace('</th','</td')
            hisdet = hisdet[hisdet.find('<td'):]
            hisbox = hisdet.split('</td>')            # creates columns
            databox = []

            for history in hisbox:    # cycles fields on the row
                h = remove_html_tags(history)
                #h = h.replace('Ready to close','Ready_to_close')
                if h != '' : databox.append(h)

            # databox has refined field values
            # lines below replace &nbsp; with date
            if databox[0] == '&nbsp;':
                    databox[0] = lastrowdate
            else:
                    lastrowdate = databox[0]

            event = databox.pop() # this is the remainder of the HTML after the final <td>


            if event.count('Changed Status from '):
                event = event.replace('Changed Status from ','')
                e1 = event[:event.find(' to ')]
                e2 = event[event.find(' to ')+4:event.find('.')]
                if e1.count('- 2L')>0:
                    e1 = 'Working on L2 Resolution' # encode 'Working on Resolution - 2L' as 'Working on L2 Resolution'
                if e1.count('- 3L')>0:
                    e1 = 'Working on L3 Resolution' # encode 'Working on Resolution - 3L' as 'Working on L3 Resolution'
                if e2.count('- 2L')>0:
                    e2 = 'Working on L2 Resolution' # encode 'Working on Resolution - 2L' as 'Working on L2 Resolution'
                if e2.count('- 3L')>0:
                    e2 = 'Working on L3 Resolution' # encode 'Working on Resolution - 3L' as 'Working on L3 Resolution'
                databox.append(e1)
                databox.append(e2)
            else:
                databox.append(event)


            if verbose > 2:
                debugit("\nDATABOX:",databox)
            # change of 24.Jan.2012:
            # due to new field in the history table connection, the number of fields we get is skewed. To resolve - pop the new field:
            event = databox.pop(2) # field "Connection is always the 3rd element
            if len(databox)==4:
                timebox.append(databox)
                if verbose > 2:
                    debugit(databox)

        # pending on support period ends on entries with status change from 'New', 'Responded' or 'Working on Resolution' to something differnet
        # the initial period is aways 'New' and has started at case_open_date

        def haskey(data):
            #debugit('LEVEL3 key: ',data)
            t = 0
            for key in support_keys:
                t = (t or data.count(key)>0)
                #t =(t or (data.count(key)>0 and data.count('L3')==0)) # excludes L3 from the support time
            return t

        def epoch(t): # returns the epoch by timestamp
            pattern = '%d/%m/%Y %H:%M'
            return int(time.mktime(time.strptime(t, pattern)))

        def day(t): # returns the date of an epoch
            pattern = '%d/%m/%Y'
            return time.strftime(pattern,time.localtime(t))

        def work_dif(endepoch,startepoch): # endepoch > startepoch
            if day(endepoch) == day(startepoch):
                if day(startepoch) != day(startepoch-5*60*60): # the support time starts at 5am, so if start_epoch_time is prior to 5am, and we substract 5h from it it will change date
                    startepoch = epoch(day(startepoch)+' 05:00')
                if day(endepoch) != day(endepoch+4*60*60): # the support time ends at 20:00 so if it's after that and we add 4h, we should end in new date
                    endepoch = epoch(day(endepoch)+' 20:00')
                rez = endepoch - startepoch
            else:
                absd = endepoch - startepoch
                if verbose >1: debugit('absolute delta in sec: ' + str(absd))
                ddays = absd // (24*60*60) # delta days (5 // 2 = 2)
                if verbose >1: debugit('div delta days:',str(ddays),' (number of days contained in the absolute delta)')
                newend = endepoch - ddays*(24*60*60)
                if verbose >1: debugit('End of period (ESD): ' + time.strftime('%d/%m/%Y %H:%M',time.localtime(endepoch)))
                if verbose >1: debugit('transposed ESD: ' + time.strftime('%d/%m/%Y %H:%M',time.localtime(newend)))
                if verbose >1: debugit('Start of period (SSD): ' + time.strftime('%d/%m/%Y %H:%M',time.localtime(startepoch)))
                rez = newend - startepoch + ddays*(15*60*60)
                if verbose >1: debugit('rez : ' + str(rez))
                if day(newend) != day(startepoch):
                    rez = rez - 9*60*60
                    if verbose >1: debugit('corrected rez : ' + str(rez))

            return rez

        support_interval = 0
        response_interval = r_endepoch = 0
        endepoch = startepoch = 0
        count = 0
        for t in timebox:
            count = count + 1
            if verbose >0: debugit(str(count)+']')
            if verbose >1: debugit('current row:',str(t))

            if haskey(t[2]) and (not haskey(t[3])): # end of time with support ######## t[2] is the "FROM" state, and t[3] is "TO" state
                endepoch = epoch(t[0])
                if verbose >1: debugit('end of time period with support ' + t[0] + ' -- in epoch ' + str(endepoch))

            # the first detected relevant event will always be "end of support time"
            # thus we can assume that we have the value for _endepoch_ already
            if (not haskey(t[2])) and haskey(t[3]): # start of time with support
                startepoch = epoch(t[0])
                if verbose >1: debugit('start of time period with support ' + t[0] + ' -- in epoch ' + str(startepoch))
                if endepoch == 0:
                    endepoch = int(time.mktime(time.localtime()))
                    if verbose > 1: debugit("ERROR start period detected prior to end period.")
                    if verbose > 0: debugit("Case still open. Assumming end of support period NOW() = " + str(endepoch))

                support_interval = support_interval + work_dif(endepoch,startepoch)
                endepoch = startepoch = 0

            if t[2].count('New')>0:
                r_endepoch = epoch(t[0])
                if verbose >1: debugit('end of RESPONSE time period with support ' + t[0] + ' -- in epoch ' + str(r_endepoch))

            if endepoch == 0:
                endepoch = int(time.mktime(time.localtime()))
                if verbose > 1: debugit("ERROR start period detected prior to end period.")
                if verbose > 0: debugit("Case still open. Assumming end of support period NOW() = " + str(endepoch))


            if verbose >1: debugit("*EndSupportTime: " + str(endepoch))
            if verbose >1: debugit("*StartSupportTime: " + str(startepoch))
            if verbose >0: debugit("*difference: " + str(support_interval))

        odd_support_interval = support_interval
        # once the cycle is over : interval = the last addtition to the pile

        if verbose >0:debugit("zodate catched in dump as " + zodate)


        startepoch = epoch(zodate)
        if verbose >1: debugit('-'*10,'response works','-'*10)
        responce_interval = work_dif(r_endepoch,startepoch)
        if verbose >1: debugit('-'*30)
        support_interval = support_interval + work_dif(endepoch,startepoch)
        if verbose >0: debugit("post cycle EndSupportTime= " + str(endepoch))
        if verbose >0: debugit("post cycle StartSupportTime= " + str(startepoch))
        if verbose >0: debugit("final diff= " + str(support_interval))
        if support_interval < 0 :
            support_interval=odd_support_interval
        if r_endepoch==0:
            # if the creation state is != New, the responce interval should be = 0
            responce_interval = 0

        return [support_interval, responce_interval]

    def debugit(*args, sep = ' ', end = '\n'):
        global log
        # print(*args,end=end)
        for a in args:
            log += str(a) + sep
        log += end

    def showit(*args, tipe = 'raw', sep = ' ', end = '\n'):
        global message
        # print('.', end = '')
        if tipe == 'raw':
            # string is directly fed into the message
            for a in args:
                message += str(a) + sep
            message += end
        else:
            # string is formated as sequence of cells in a table row
            message += '<tr>'
            for a in args:
                message += '<td>' + str(a) + '</td>'
            message += '</tr>' + end

    def get_caselist(account, connection):
        _pages=[]
        if account == 'wlk':
            for page in range(pages_back):
                # call to POST desired table rows and filter/sorting                                                                                                                                                           retURL=%2F500%3Ffcf%3D00B20000004wphi%26rolodexIndex%3D-1%26page%3D1&isdtp=null
                # clsoed
                txdata = 'action=filter&filterId=00B20000004wphi&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&vf=undefined&retURL=%2F500%3Ffcf%3D00B20000004wphi%26rolodexIndex%3D-1%26page%3D1&isdtp=null'
                # all open
                txdata = 'action=newfilter&filterId=00B20000005XOp6&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=&rolodexIndex=-1&retURL=%2F500%3Ffcf%3D00B20000004wpi7%26rolodexIndex%3D-1%26page%3D1'
                connection.handle.setdata(txdata)
                connection.handle.setref('https://eu1.salesforce.com/500?fcf=00B20000004wphi')
                udata = connection.sfcall('https://eu1.salesforce.com/_ui/common/list/ListServlet') # list of closed cases
                _pages.append(udata)
        elif account == 'st':
            for page in range(pages_back):
                # call to POST desired table rows and filter/sorting
                # view007
                txdata =    'action=filter&filterId=00B20000005EOlZ&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&retURL=%2F500%3Ffcf%00B20000005EOlZ%26rolodexIndex%3D-1%26page%3D1'
                # all open
                txdata = 'action=newfilter&filterId=00B20000000nD39&filterType=t&page='+str(page+1)+'&rowsPerPage='+num_records_to_pull+'&search=&sort=-CASES.CASE_NUMBER&rolodexIndex=-1&retURL=%2F500%3Ffcf%3D00B20000005EOlZ%26rolodexIndex%3D-1%26page%3D1'
                connection.handle.setdata(txdata)
                connection.handle.setref('https://emea.salesforce.com/500?fcf=00B20000005EOlZ')
                udata = connection.sfcall('https://emea.salesforce.com/_ui/common/list/ListServlet')
                _pages.append(udata)
        else:
            debugit('errror - wrong account identifier: ',account)

        # debugit('len st pages:',len(_pages))
        return _pages

    def logout(account, connection):
        if account == 'wlk':
            pass
            # txdata = ''
            # connection.handle.setdata(txdata)
            # connection.handle.setref('https://eu1.salesforce.com/500?fcf=00B20000004wphi')
            # udata = connection.sfcall('https://emea.salesforce.com/secur/logout.jsp') # list of closed cases
        elif account == 'st':
            pass
            # txdata = ''
            # connection.handle.setdata(txdata)
            # connection.handle.setref('https://emea.salesforce.com/500?fcf=00B20000005EOlZ')
            # udata = connection.sfcall('https://emea.salesforce.com/secur/logout.jsp')
        else:
            debugit('errror - wrong account identifier: ', account)

        debugit('RAW LOGOUT DUMP:',udata)
        return True

    def parse_pages(account, pages):
        cardlist = []
        for udata in pages:
            if debug > 1:
                debugit('ACCOUNT:',account,'\nLIST OF CASES UDATA:',udata)
            if debug > 0:
                try:
                    with open('c:\\temp\\stsfbot_dump1.txt','w') as ff:
                        ff.write(udata)
                except UnicodeEncodeError as e:
                    debugit('eeerror:',e)
            #### The parser works over html result of ST case view ---
            case_created_str = udata[udata.find('CASES.CREATED_DATE":')+20:]
            case_created_str = case_created_str[:case_created_str.find('],')+1]
            if debug > 0: debugit(case_created_str)
            # case_created_str = 'case_created_box = ' + case_created_str
            # exec(case_created_str)
            case_created_box = case_created_str[1:-1].split(',')
            case_created_box = [ z.strip('"') for z in case_created_box]
            #debug =0
            if debug > 0: debugit(case_created_box)
            if debug > 1: debugit('********************************************************************')

            case_link_str = udata[udata.find('CASES.CASE_NUMBER":[')+20:]
            case_link_str = case_link_str[:case_link_str.find('],')]
            case_link_str = case_link_str.replace('"u003Ca href="','')
            case_link_str = case_link_str.replace('u003C/au003E"','')
            case_link_str = case_link_str.replace('"u003E','*')
            case_link_box = case_link_str.split(',/')
            # clear the initial "/" from the 1st element
            case_link_box[0] = case_link_box[0][1:]
            if debug > 0: debugit(case_link_box)
            if debug > 1: debugit('********************************************************************')

            #verify the indexation
            conditional_debug = 0
            targetlen = len(case_created_box)
            if len(case_link_box) != targetlen: conditional_debug = 1
            #if len(case_closed_box) != targetlen: conditional_debug=1
            #if len(case_sever_box) != targetlen: conditional_debug=1
            if conditional_debug == 1: debugit("ERROR - difference in the boxes indexation")
            if conditional_debug > 0: debugit('starts: '+ str(len(case_created_box)))
            if conditional_debug > 0: debugit('links: '+ str(len(case_link_box)))
            #if conditional_debug > 0: debugit('closes: '+ str(len(case_closed_box)))
            #if conditional_debug > 0: debugit('sevirities: '+ str(len(case_sever_box)))

            for i in range(len(case_created_box)): # #for i in range(22,24):
                card = {}
                #if case_created_box[i].find(target_month)>0:
                tmp = case_link_box[i].split('*')
                if debug > 0:
                    debugit('to split <id> and <link> - searching * in item #', i, 'in the case_link_box[i]=', case_link_box[i], '. Result is:', tmp)
                try:
                    card['id'] = tmp[1] # id
                except IndexError as e:
                    with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
                        ff.write(log)
                card['link'] = tmp[0] # link
                #card['severity'] = case_sever_box[i] # severity
                card['created'] = case_created_box[i] # created
                #card['closed'] = case_closed_box[i] # closed

                cardlist.append(card)

        # debugit('\n\n')
        if debug > 0:
            debugit('number of new records requested:' + num_records_to_pull)
            debugit('number of pages requested:' + str(pages_back))
            debugit('-'*30)
        return cardlist

    def capture_case_details(cardlist, account, connection):
        bigbox =[]
        # counts = {'outslacount': 0,'outrespsla':0,'outslacomb':0}
        for card in cardlist:  # walk em case by case and extend the data in each CARD
            if debug > 0:
                debugit('ACCOUNT:',account,'CARD:',card)
                try:
                    with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
                        ff.write(log)
                except UnicodeEncodeError as e:
                    print("Error creating log file:",e)
                    # print(log.encode('utf8'))
                # with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
                #     ff.write(log)
            if account == 'wlk':
                #call (7)
                connection.handle.setref('https://eu1.salesforce.com/500/o')
                udata = connection.sfcall('https://eu1.salesforce.com/'+card['link']+'?rowsperlist=30') #https://emea.salesforce.com/5002000000EI92C?rowsperlist=25 #details of a case
                udata = udata.replace('u003C','<')
                udata = udata.replace('u003E','>')
                card['udata'] = udata # !!! scary

                system = udata[udata.find('00N200000023Rfa_ileinner">')+26:]
                system = system[:system.find('</div></td><td class="labelCol">Contact Email')]
                card['system'] = system

                #get severity
                #Severity   ... Severity 2   ...    3rd Party Case ID      ;;;; _ileinner">Severity 2</div>
                zsev = parse(udata,'Severity ','3rd Party Case ID')
                card['severity'] = zsev[0]

                #get subject
                zsub = parse(udata,'labelCol">Subject','Description')
                card['subject'] = remove_html_tags(zsub).strip('\n')

                # determine SLA
                sla=0
                #if system=="Ferry+" or system=="Local PC / network access" or system=="Email" or system=="Local PC" or system=="Wide Area Network" or system=="Sentinel":
                if system=="Ferry+" or system=="Local PC" or system=="Email" or system=="Wide Area Network" or system=="Sentinel":
                    if card['severity']=="Severity 1": sla = 1
                    elif card['severity']=="Severity 2": sla = 8
                    else: sla = 15

                elif system=="DRS" or system=="CDI" or system=="Blackberry Server":
                    if card['severity']=="Severity 1": sla = 3
                    elif card['severity']=="Severity 2": sla = 8
                    else: sla=15

                elif system=="Profit Optimisation (RTS)" or system=="Great Plains" or system=="RPO" or system=="Intranet":
                    if card['severity']=="Severity 1": sla = 4
                    elif card['severity']=="Severity 2": sla = 8
                    else: sla= 15

                elif system=="CRM" or system=="Document Management" or system=="Sailing Statistics (AIS)":
                    if card['severity']=="Severity 1": sla = 8
                    elif card['severity']=="Severity 2": sla = 15
                    else: sla = 22

                else: print("Unknown system: " + system + '(' + card['link'] + ')')
                card['sla'] = sla

                zstatus = parse(udata,'Status</td>','</div></td>')
                card['status'] = remove_html_tags(zstatus)
                # get closetime
                #<div id="ClosedDate_ileinner">29/05/2011 13:54</div></td></tr>\n<tr><td class="labelCol last">C
                zclosedate = parse(udata,'ClosedDate_ileinner">','</div>')
                card['closedate'] = zclosedate
            elif account == 'st':
                #call (7)
                connection.handle.setref('https://emea.salesforce.com/500/o')
                if debug > 0: debugit(card)#['link'])
                udata = connection.sfcall('https://emea.salesforce.com/'+card['link']+'?rowsperlist=100',1) #https://emea.salesforce.com/5002000000EI92C?rowsperlist=25 #details of a case
                udata = udata.replace('u003C','<')
                udata = udata.replace('u003E','>')
                card['udata'] = udata # !!! scary

                #<td class="labelCol">Type</td><td class="dataCol">Problem</td></tr>\n<tr><td class="labelCol">Status</td>
                zproblem = parse(udata,'Type</td>','>Status</td>')
                card['problem'] = remove_html_tags( parse(zproblem,'">','</td>'))
                #<td class="labelCol">Status</td>
                zstatus = parse(udata,'Status</td>','>Account Name</td>')
                card['status'] = remove_html_tags( parse(zstatus,'">','</td>'))
                zreason = parse(udata,'Case Reason</td>','>Support Priority</td>')
                card['reason'] = remove_html_tags( parse(zreason,'">','</td>'))
                zsubject = parse(udata,'Subject</td>','>Description</td>')
                card['subject'] = remove_html_tags( parse(zsubject,'">','</td>'))
                card['sla'] = -1
                if card['problem'] == 'Problem': card['sla'] = 16
                if card['problem'] == 'Feature Request': card['sla'] = 9999
                if card['problem'] == 'Question': card['sla'] = 8
                #<td class="labelCol">Case Reason</td><td class="dataCol">Complex Functionality</td></tr>\n<tr><td class="labelCol">Support Priority</td>
                zreason = parse(udata,'Case Reason</td>','>Support Priority</td>')
                zreason = parse(zreason,'">','</td>')
                #w</td><td class="labelCol">Date/Time Closed</td><td class="dataCol">24/05/2011 11:08</td></tr>\n<tr><td class="labelCol">Resolution Reason
                zclosedate = parse(udata,'Date/Time Closed</td><td class="dataCol">','</td>')
                card['closedate'] = zclosedate

                #Account Name   Bauer Corporate Services UK \n Product
                zclient = parse(udata,'Account Name','Product')
                zclient = remove_html_tags(zclient)
                #debugit(zclient)
                card['client'] = zclient.strip()

                if card['reason'] == 'License Request':
                    card['sla'] = 2
                    if card['sla'] != -1:
                        debugit("Overwriting SLA: " + str(card['sla']))

            #capture comment info
            comment_table = parse(udata,'<th scope="col" class=" zen-deemphasize">Comment</th>','</table>')
            # Created By: <a href="/00520000000kQ05">StressTester Support</a> (05/03/2013 19:00)</b>
            zcomments = re.findall(r'Created By: <a href=".+?">(.+?)</a> (.+?)</b>(.+?)</td></tr>', comment_table)
            comment_bucket = []
            #debugit('zcomments')#,zcomments)
            if len(zcomments) > 0:
                for comm in zcomments:
                    if comm[1].count('|')>0:
                        comment_bucket.append( (comm[0],comm[1][:comm[1].find('|')-1].strip('()'), comm[2]) )
                    else:
                        comment_bucket.append( (comm[0],comm[1].strip('()'), comm[2]) )
                    #debugit(comment_bucket[-1])
            else:
                comment_bucket = []

            card['comments'] = comment_bucket

            # #####################################################################################
            # ########### part of cycling all/new cases where we print the SLA result #############
            # #####################################################################################
            rez = card['casetimes'] = casetimes(card['created'],udata,card['link']) # returns the support time in sec; type=long.

            bigbox.append(card)

        return bigbox

    def find_chase_miss(cardlist):
        chase_miss = []
        postponed_chase = []
        #for card in bigbox:
        for card in cardlist:
            if 1==0: # enable to see full list of open cases
                debugit('Case:', card['id'], end=' ')
                for key in card.keys():
                    if key != 'id' and key != 'udata' and key != 'closedate':
                        if key == 'comments':
                            debugit(key, ': ', [ z[:-1] for z in card[key] ],'; ', end = '')
                        else:
                            debugit(key, ': ', card[key], '; ', end = '')

                debugit()

            # push back chase based on 'Logged as Defect'
            if card['status'] == 'Logged as Defect':
                should_have_chase_since = last_wednesday
            else:
                should_have_chase_since = today
            card['target_chase'] = should_have_chase_since
            card['chase_state'] = 'chased'
            # push back chase based on executed chase or 'resume chasing on'
            if len(card['comments']) > 0:
                if debug>0:
                    debugit('card:', card)
                chased = False
                
                comment = card['comments'][0] ## the latest comment
                if debug > 0:
                    debugit('comment:', comment)
                comment_date = datetime.datetime.strptime(comment[1], '%d/%m/%Y %H:%M')

                #chased
                # debugit('comparing', comment_date, '>', should_have_chase_since, '=', comment_date > should_have_chase_since, 'chased', chased)
                if (comment[0] == 'StressTester Support' or comment[0] == 'Wightlink Support Team') and comment_date > should_have_chase_since:
                    chased = True

                #postponed
                if comment[2].lower().count('resume chasing') > 0 or comment[2].lower().count('resume chase') > 0:
                    postpones = re.findall(r'resume chas(e|ing)( on){0,1} {0,2}(../../....)', comment[2], flags=re.IGNORECASE)

                    if len(postpones) > 0:
                        # find if there is client comment after the postpone comment
                        has_subsequent_comment = card['comments'].index(comment) != 0
                        postpone = postpones[0][2]
                        postpone_date = datetime.datetime.strptime(postpone, '%d/%m/%Y')
                        if postpone_date > today and not has_subsequent_comment:
                            chased = True
                            card['postpone'] = str(postpone_date)
                            postponed_chase.append(card)
                            card['chase_state'] = 'postponed'
                    else:
                        debugit('ERRORNEOUS POSTPONE MESSAGE', comment[2], card['id'])

                # resume postpone == ignore subsequent comments
                repostpone = re.findall(r'resume {0,3}postpone', comment[2], flags=re.IGNORECASE)
                if len(repostpone) > 0:
                    for comm in card['comments']:
                        if comm[2].lower().count('resume chasing') > 0 or comm[2].lower().count('resume chase') > 0:
                            postpones = re.findall(r'resume chas(e|ing)( on){0,1} {0,2}(../../....)', comm[2], flags=re.IGNORECASE)
                            if len(postpones) > 0:
                                break

                    postpone = postpones[0][2]
                    postpone_date = datetime.datetime.strptime(postpone, '%d/%m/%Y')
                    if postpone_date > today:
                        chased = True
                        card['postpone'] = str(postpone_date)
                        postponed_chase.append(card)
                        card['chase_state'] = 'postponed'

                if not chased:
                    chase_miss.append(card)
                    card['chase_state'] = 'missed'

        return chase_miss, postponed_chase, cardlist

    def set_connection(account):
        if account == 'wlk':
            try:
                os.remove('d:/temp/wlk_sfcookie.pickle')
            except:
                pass
            connection = sfuser('wlk')
            connection.setdir('d:/temp/')
            connection.setdebug(myweb_module_debug)
            connection.sflogin()
            support_keys = ['New', 'In Progress', 'Responded', ]#'Waiting on user','With 3rd Party',]
        else:
            connection = sfuser('st')
            connection.setdir('d:/temp/')
            connection.setdebug(myweb_module_debug)
            connection.sflogin()
            support_keys = ['New', 'Responded', 'Working on Resolution', ]#'Working on L2 Resolution',]# 'Working on L3 Resolution', ]

        return connection, support_keys

                #####################################################################################
    #-----------########========------ END OF INTERNAL SUBROUTINES DEFINITIONS ------========########----------#
                #####################################################################################

    global today
    global log
    log = ''
    global message
    message = ''
    # showit('destination: ', TOADDRS, '<br>')
    # push back chase since based on weekend
    lastBusDay = datetime.datetime.today()
    if datetime.date.weekday(lastBusDay) == 5:      #if it's Saturday
        lastBusDay = lastBusDay - datetime.timedelta(days = 1) #then make it Friday
    elif datetime.date.weekday(lastBusDay) == 6:      #if it's Sunday
        lastBusDay = lastBusDay - datetime.timedelta(days = 2); #then make it Friday
    else:
        lastBusDay = datetime.date.today()
    today = datetime.datetime.combine(lastBusDay, datetime.time(0, 0))


    # prepare last Wednesday as date
    offset = (today.weekday() - 2) % 7
    last_wednesday = today - datetime.timedelta(days = offset)
    showit('comparing against dates', '<br>')
    showit('&nbsp;*&nbsp; today:', str(today), '<br>')
    showit('&nbsp;*&nbsp; last Wed:', str(last_wednesday), '<br><br>')

    accounts = { 'st': {'today': today, 'last_wednesday': last_wednesday, 'cardlist': []}, 'wlk': {'today': today, 'last_wednesday': last_wednesday, 'cardlist': []} }
    # cycle accounts
    for account in accounts.keys():
        if debug >0:
            debugit('PROCESSING ACCOUNT:', account)
        showit('='*20, account.upper(), 'CHASE MISS\n', '='*20, '<br>')
        connection, support_keys = set_connection(account)
        pages = get_caselist(account, connection)
        cardlist = parse_pages(account, pages)
        # connection.handle.close() # this is mover to the end of the <account> cycle

        if debug > 0:
            debugit('PAGES:', pages)
            debugit('CARDLIST:', cardlist)
            debugit('-='*20)
            # with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
            #     ff.write(log)
            try:
                with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
                    ff.write(log)
            except UnicodeEncodeError as e:
                print("Error creating log file:",e)
                # print(log.encode('utf8'))
       
        if len(cardlist)>0:
            cardlist = capture_case_details(cardlist, account, connection)
        else:
            showit('No open cases<br>')

        for card in cardlist:
            card['last_comment'] = card['comments'][0][:-1]
            if 'postpone' not in card:
                card['postpone'] = '-'
        
        # cardlist = sorted(cardlist, key = lambda x: int(x['id']))
        chase_miss, postponed_chase, tmp_cardlist = find_chase_miss(cardlist)
        cardlist = tmp_cardlist
        showit('<table>')
        showit('States considered as pending to support:', str(support_keys), tipe = 'tbl')
        showit('Open Cases Total Count:', str(len(cardlist)), tipe = 'tbl')
        showit('Cases to Chase Count:', str(len(chase_miss)), tipe = 'tbl')
        showit('Cases with "Postponed Chase" Count: ', str(len(postponed_chase)), tipe = 'tbl')
        showit('</table><br>')
        showit('<br>To Chase:')
        if len(chase_miss) > 0:
            showit('<table style="border:1px solid black; padding:5px;">\n<tr><th>Case</th><th>Status</th><th>Subject</th><th>Last Comment</th><th>postpone chase</th><th>target chase</th></tr>')
            for card in chase_miss:
                showit(card['id'], card['status'], card['subject'], card['last_comment'], card['postpone'], card['target_chase'], tipe = 'tbl')
            showit('</table>')
        else:
            showit('Nothing to chase<br>')

        if len(postponed_chase) > 0:# and destination != 'team':
            showit('<br>Postponed:')
            showit('<table style="border:1px solid black; padding:5px;">\n<tr><th>Case</th><th>Status</th><th>Subject</th><th>Last Comment</th><th>postpone chase</th><th>target chase</th></tr>')
            for card in postponed_chase:
                # if 'postpone' in card:
                #     postpone = card['postpone']
                # else:
                #     postpone = '-'
                # last_comment = card['comments'][0][:-1]
                showit(card['id'], card['status'], card['subject'], card['last_comment'], card['postpone'], card['target_chase'], tipe = 'tbl')
            showit('</table>')
        showit('<br><br>')

        #fill in the values for cardlist in the big accounts dictionary
        accounts[account]['cardlist'] = cardlist

        #destroy connection of the processed account
        connection.close()

        # WRITE LOG & LOGOUT
        if debug > 0:
            try:
                with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
                    ff.write(log)
            except UnicodeEncodeError as e:
                print("Error creating log file:",e)
                # print(log.encode('utf8'))

        # logout(account,connection)

    # showit('</div></body></html>')

    # the current message will be wrapped in HTML hearde/footer for email and file displaying
    full_message = '''<html>
    <style>
    body{
    font-family:\"Lucida Grande\", \"Lucida Sans Unicode\", Verdana, Arial, Helvetica, sans-serif; font-size:18px; }
    p, h1, form, button { border:0; margin:0; padding:0; }
    th, td { font-size:14px; border:1px solid black; padding:5px; }
    </style>
    <body>
    <div id=\"stylized\" class=\"myblock\">
    <h1>Chasing</h1>''' + message + '</div></body></html>'

    if debug > 0:
        try:
            with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
                ff.write(log)
        except UnicodeEncodeError as e:
            print("Error creating log file:",e)
            # print(log.encode('utf8'))
        # with open('c:/gits/django2wrap/run_debug_results.txt','w') as ff:
        #     ff.write(log)

    return message, full_message, accounts, today, last_wednesday
    
def mailit(message):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from time import localtime, strftime
    subject  = "Daily Chase Status " + strftime("%H:%M", localtime())

    # inclusion ---------------------------------------------
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = FROMADDR
    msg['To'] = ','.join(TOADDRS)

    # Create the body of the message (a plain-text and an HTML version).
    # text = "this message is not available in plain text"
    # part1 = MIMEText(text, 'plain')
    part2 = MIMEText(message, 'html', 'utf-8')
    # msg.attach(part1)
    msg.attach(part2)
    # end of inclusion --------------------------------------

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.set_debuglevel(0)
    server.ehlo()
    server.starttls()
    server.login(LOGIN, PASSWORD)
    server.sendmail(FROMADDR, TOADDRS, msg.as_string())
    server.quit()
