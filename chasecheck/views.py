# coding: utf-8
from django.template.response import TemplateResponse
from django.shortcuts import render
import time, os
from . import chase as chaser

def chase(request):
    last_time = time.ctime(os.path.getmtime(chaser.LAST_REUSLTS))
    if request.method == "POST":
        message, full_message, accounts, today, last_wednesday = chaser.main_chase()

        column_list = ['id', 'status', 'subject', 'last_comment', 'postpone', 'target_chase']

        wlk_total_list = accounts['wlk']['cardlist']
        # wlk_list_keys = wlk_total_list[0].keys()
        wlk_total = len(wlk_total_list)
        wlk_to_chase_list = [z for z in wlk_total_list if z['chase_state'] == 'missed']
        wlk_to_chase = len(wlk_to_chase_list)
        wlk_postponed_list = [z for z in wlk_total_list if z['chase_state'] == 'postponed']
        wlk_postponed = len(wlk_postponed_list)

        st_total_list = accounts['st']['cardlist']
        st_total = len(st_total_list)
        st_to_chase_list = [z for z in st_total_list if z['chase_state'] == 'missed'] 
        st_to_chase = len(st_to_chase_list)
        st_postponed_list = [z for z in st_total_list if z['chase_state'] == 'postponed']
        st_postponed = len(st_postponed_list)
        
        # all_posts = request.POST
        if "sendit" in request.POST.keys():
            chaser.mailit(full_message)

        # result = render(request, 'chase.html', locals())
        result = TemplateResponse(request, 'chase.html', locals())
        with open(chaser.LAST_REUSLTS,'w') as fff:
            fff.write(result.rendered_content)

    else:
        result = render(request, 'chase.html', locals())

    return result

def results(request):
    return render(request, 'last_chase_ruslts.html', locals())

