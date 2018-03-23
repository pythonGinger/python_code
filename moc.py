#!/usr/bin/env python
#-*-coding:utf-8-*-
from bs4 import BeautifulSoup as BS
import urllib, urllib2, cookielib
import matplotlib.pyplot as plt
from getpass import getpass
from PIL import Image
import hashlib
import random
import json
import time
import ssl
import re
import os

def global_var():

    global DOMAIN, REFERER, CAPTCHA_URL, LOGIN_URL, HEADERS, URLOPENER, QUESTION_ANSWER
    DOMAIN = 'https://mooc1-2.chaoxing.com'
    REFERER = 'http://i.mooc.chaoxing.com'
    CAPTCHA_URL = 'http://passport2.chaoxing.com/num/code'
    LOGIN_URL = 'http://passport2.chaoxing.com/login?refer=http://i.mooc.chaoxing.com'
    HEADERS = {}
    HEADERS['Referer'] = DOMAIN
    HEADERS['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0'
    ssl._create_default_https_context = ssl._create_unverified_context#deal with the SSL error
    cookiejar = cookielib.CookieJar()
    URLOPENER = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))#a container save cookie
    with open ("./question_and_answer.json", "r") as f:
        QUESTION_ANSWER = json.load(f)

def login():

    while True:

        HEADERS['Referer'] = REFERER
        req = urllib2.Request(LOGIN_URL, headers=HEADERS)
        rsp = URLOPENER.open(req)
        captcha_content = URLOPENER.open(CAPTCHA_URL).read()
        with open ('temp/num_capcha.jpeg', 'wb') as f:
            f.write(captcha_content)
        captcha_img = Image.open('temp/num_capcha.jpeg')
        username = raw_input('Username: ')
        password = getpass('Password: ')
        plt.figure("captcha")
        plt.imshow(captcha_img)
        plt.ion()
        plt.pause(0.1)
        captcha = raw_input('Captcha: ')
        login_form = {}
        login_form['fid'] = '21383'
        login_form['uname'] = username
        login_form['password'] = password
        login_form['numcode'] = captcha
        HEADERS['Referer'] = LOGIN_URL
        data = urllib.urlencode(login_form)#encode parameters
        post_form = urllib2.Request(LOGIN_URL, headers=HEADERS, data=data)
        post_rsp = URLOPENER.open(post_form).read()
        if 'settings/info' in post_rsp:
            mark_right_captcha(captcha_img, captcha, "numcode")
            plt.close("captcha")
            print 'Login successfully !'
            break
        else:
            print 'Please check your username, password and captcha !\nMake sure you enter them right !'

def setup_savepath():

    dirs = ['alpha_captcha', 'num_capcha', 'temp']
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)

def get_mycourse_url():

    mycourse_page = 'http://mooc1-2.chaoxing.com/visit/courses'# Get course info
    mycourse_request = urllib2.Request(mycourse_page, headers=HEADERS)
    mycourse_response = URLOPENER.open(mycourse_request).read()
    mycourse_pattern = r'/mycourse/studentcourse+.+courseId=\d{9}&clazzid=\d{7}&enc=\w{32}' # Get courseId, clazzId, enc
    mycourse = re.findall(mycourse_pattern, mycourse_response)[0] # at present I have only one course
    course_url = DOMAIN + mycourse
    return course_url

def get_chapter_url(course_url):

    course_request = urllib2.Request(course_url, headers=HEADERS) # the page contain the chapter info
    course_response = URLOPENER.open(course_request).read()
    soup = BS(course_response, 'html.parser')
    chapter_detail = [] # detail: clazzId, courseid, chapterid
    for link in soup.find_all('a'):
        href = link.get('href')
        if len(href) == 114:
            clazzid = href[70:77]
            courseid = href[52:61]
            chapterid = href[33:42]
            #enc = href[82:]
            chapter_detail.append((clazzid, courseid, chapterid))
            #print(clazzid, courseid, chapterid, enc)
    return chapter_detail
    #There are many noise in the page for the reason why I choose BeautifulSoup instead of re to match the href

def watch_video_and_do_homework(chapter_detail):

    validate_flag = 'off'
    for detail in chapter_detail:
        clazzid, courseid, knowledgeid = detail
        print "clazzId: %s, courseId: %s, knowledgeId: %s" % (clazzid, courseid, knowledgeid)
        for num in range(2):
            video_url = DOMAIN + '/knowledge/cards?clazzid=%s&courseid=%s&knowledgeid=%s&num=%d&v=20160407-1' % (clazzid, courseid, knowledgeid, num)
            video_request = urllib2.Request(video_url, headers=HEADERS)
            video_response = URLOPENER.open(video_request).read()
            soup = BS(video_response, 'html.parser')
            if len(soup.title.get_text()) == 2:
                watch_video(video_response)
                feedback = redirect(clazzid, courseid, knowledgeid, num, validate_flag)
                if feedback == 'on':
                    validate_flag = 'on'
                time.sleep(5)
                break

def redirect(clazzid, courseid, knowledgeid, num, validate_flag):

    question_url = DOMAIN + '/knowledge/cards?clazzid=%s&courseid=%s&knowledgeid=%s&num=%d&v=20160407-1' % (clazzid, courseid, knowledgeid, num+1)
    request = urllib2.Request(question_url, headers=HEADERS)
    response = URLOPENER.open(request).read()
    info_json = match_info(response)
    jobid = info_json['attachments'][0]['property']['jobid']
    knowledgeid = info_json['defaults']['knowledgeid']
    clazzId = info_json['defaults']['clazzId']
    enc = info_json['attachments'][0]['enc']
    courseid = info_json['defaults']['courseid']
    utenc = 'fe1733183354a56a6a4a1fca2cb6785d'
    workId = jobid.replace('work-', '')
    question_url = """
    https://mooc1-2.chaoxing.com/api/work?api=1&workId=%s&jobid=%s&needRedirect=true&knowledgeid=%s&ut=s&clazzId=%s&type=&enc=%s&utenc=%s&courseid=%s
    """ % (workId, jobid, knowledgeid, clazzId, enc, utenc, courseid)
    question_req = urllib2.Request(question_url, headers=HEADERS)
    question_rsp = URLOPENER.open(question_req).read()
    action_pattern = r'addStudentWorkNewWeb+.+_classId=\d{7}&courseid=\d{9}&token=\w{32}&totalQuestionNum=\w{32}'
    actions = re.findall(action_pattern, question_rsp)
    if actions:
        form_action = DOMAIN + '/work/' + actions[0]
        do_homework(question_rsp, question_url, form_action, validate_flag)
        return 'on'
    else:
        scrapy_question_answer(question_rsp)
        return 'off'

def match_info(response):

    pattern = r'{"attachments"+.+"control":true}'
    batch = re.findall(pattern, response)[0]
    return json.loads(batch)
    #print json.dumps(json.loads(batch), sort_keys=True, indent=4, separators=(',', ':'))
    #for debug and find the important info I make the info_json more pretty

def scrapy_question_answer(question_rsp):

    keys = []
    soup = BS(question_rsp, 'html.parser')
    for div in soup.find_all('div'):
        if div.has_attr('style') and not div.has_attr('class'):
            question = div.get_text().encode('utf-8').strip()
            if question != '':
                if '【单选题】' in question:
                    keys.append([question, 0])
                elif '【判断题】' in question:
                    keys.append([question, 3])
                print question
    k = 0
    for span in soup.find_all('span'):
        answer = span.get_text().encode('utf-8').strip()
        if '我的答案：' in answer:
            my_answer = answer.replace('我的答案：', '').replace('√', 'true').replace('×', 'false')
            keys[k].append(my_answer)
            k += 1
        print answer
    for a in soup.find_all('a'):
        print a.previous_sibling.get_text(), a.get_text()

def query_right_answer(question):

    question_key = question.decode("utf-8")
    answer = QUESTION_ANSWER.get(question_key)
    if answer == None:
        if "单选题" in question:
            choices = ["A", "B", "C", "D"]
            answer = random.choice(choices)
        elif "判断题" in question:
            choices = ["true", "false"]
            answer = random.choice(choices)
    return answer

def do_homework(question_rsp, question_url, form_action, validate_flag):

    answers = []
    answerid = []
    answerwqbid = ''
    answerid_pattern = r'answertype\d{6,8}'
    rough_answerid = re.findall(answerid_pattern, question_rsp)
    for aid in rough_answerid:
        if aid.replace('type', '') not in answerid:
            answerwqbid += '%s,' % aid.replace('answertype', '')
            answerid.append(aid.replace('type', ''))
    soup = BS(question_rsp, 'html.parser')
    for div in soup.find_all('div', 'clearfix'):
        if div.has_attr('style') and div.has_attr('class'):
            question = div.get_text().encode('utf-8').strip()
            right_answer = query_right_answer(question)
            answers.append(right_answer)
            print question, right_answer
    params = {}
    for ipt in soup.find_all('input'):
        param_name = ipt['name']
        try:
            value = ipt['value']
            if value not in 'ABCDtruefalse':
                params[param_name] = value
        except Exception as e:
            value = ""
            if param_name == "answerwqbid":
                value = answerwqbid
            params[param_name] = value
    for index, anid in enumerate(answerid):
        answer = answers[index]
        answer_id = anid
        params[answer_id] = answer
    fuck_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0", "Referer": question_url}
    if validate_flag == 'on':
        params = validate_before_handin(question_url, fuck_headers, params)
    handin_homework(form_action, fuck_headers, params)
    print json.dumps(params, sort_keys=False, indent=4, separators=(',', ':'))

def validate_before_handin(question_url, fuck_headers, params):

    while True:
        captcha_url = 'https://mooc1-2.chaoxing.com/img/code'
        validate_url = 'https://mooc1-2.chaoxing.com/img/ajaxValidate2'
        req = urllib2.Request(captcha_url, headers=fuck_headers)
        captcha_img_content = URLOPENER.open(req).read()
        with open ('temp/alpha_code.jpeg', 'wb') as f:
            f.write(captcha_img_content)
        captcha_img = Image.open('temp/alpha_code.jpeg')
        plt.figure("captcha")
        plt.imshow(captcha_img)
        plt.ion()
        plt.pause(0.1)
        captcha = raw_input('Captcha: ')
        captcha_validate_form = {}
        captcha_validate_form['code'] = captcha
        data = urllib.urlencode(captcha_validate_form)
        captcha_validate = urllib2.Request(validate_url, headers=fuck_headers, data=data)
        validate_rsp = URLOPENER.open(captcha_validate).read()
        json_rsp = json.loads(validate_rsp)
        if json_rsp["status"] == True:
            params["enc"] = json_rsp["enc"]
            mark_right_captcha(captcha_img, captcha, "alphacode")
            return params
        else:
            print 'Wrong captcha !'

def handin_homework(form_action, fuck_headers, params):

    form = urllib.urlencode(params)
    form_action = form_action + '&version=1&ua=pc&formType=post&saveStatus=1&pos=&value='
    req = urllib2.Request(form_action, data=form, headers=fuck_headers)
    rsp = URLOPENER.open(req).read()

def watch_video(video_response):

    info_json = match_info(video_response)
    otherInfo = info_json['attachments'][0]['otherInfo']
    objectId = info_json['attachments'][0]['objectId']
    jobid = info_json['attachments'][0]['jobid']
    userid = info_json['defaults']['userid']
    clazzId = info_json['defaults']['clazzId']
    duration, dtoken = get_duration_dtoken(objectId)
    clipTime_list = []
    clipTime_end = '0_' + str(duration)
    clipTime_before_end = '0_' + str(duration-1)
    clipTime_list.append(clipTime_end)
    clipTime_list.append(clipTime_before_end)
    interval = 60
    process_list = []
    process_list.append(duration-1)
    process_list.append(duration)
    for process in process_list:
        for clipTime in clipTime_list:
            enc = encrypt_playingTime(clazzId, userid, jobid, objectId, process, duration, clipTime)
            feedback = report(dtoken, otherInfo, userid, jobid, clipTime, objectId, clazzId, duration, process, enc)
            if feedback == "next":
                return

def get_duration_dtoken(objectId):

    status_url = 'https://mooc1-2.chaoxing.com/ananas/status/' + objectId
    request = urllib2.Request(status_url, headers=HEADERS)
    response = URLOPENER.open(request).read()
    json_rep = json.loads(response)
    duration = json_rep['duration']
    dtoken = json_rep['dtoken']
    return duration, dtoken

def encrypt_playingTime(clazzId, userid, jobid, objectId, process, duration, clipTime):

    salt = 'd_yHJ!$pdA~5'
    encrypt_method = "[{}][{}][{}][{}][{}][{}][{}][{}]".format(clazzId, userid, jobid, objectId, process*1000, salt, duration*1000, clipTime)
    md5 = hashlib.md5()
    md5.update(encrypt_method.encode('utf-8'))
    enc = md5.hexdigest()
    return enc

def report(dtoken, otherInfo, userid, jobid, clipTime, objectId, clazzId, duration, playingTime, enc):

    play_report_url = """
    https://mooc1-2.chaoxing.com/multimedia/log/%s?otherInfo=%s&userid=%s&rt=0.9&jobid=%s&clipTime=%s&dtype=Video&objectId=%s&clazzId=%s&duration=%s&view=pc&playingTime=%s&isdrag=3&enc=%s
    """ % (dtoken, otherInfo, userid, jobid, clipTime, objectId, clazzId, duration, playingTime, enc)
    request = urllib2.Request(play_report_url, headers=HEADERS)
    response = URLOPENER.open(request).read()
    if 'true' in response:
        print '^_^Passed Time: %s! ^_^' % playingTime
        return "next"
    else:
        print 'Reporting time: %s...' % playingTime
        return "continue"

def mark_right_captcha(captcha_img, right_captcha, captcha_type):

    if captcha_type == 'numcode':
        savepath = 'num_capcha'
    elif captcha_type == 'alphacode':
        savepath = 'alpha_captcha'
    a_copy = captcha_img.copy()
    right_captcha_no = len(os.listdir(savepath))+1
    right_captcha_name = '%s/%s-%d.jpeg' % (savepath, right_captcha, right_captcha_no)
    a_copy.save(right_captcha_name)

def logout():

    out_url = 'https://passport2.chaoxing.com/logout.html?'
    out_req = urllib2.Request(out_url, headers=HEADERS)
    out_rep = URLOPENER.open(out_url).read()

def engine():

    setup_savepath()
    global_var()
    login()
    course_url = get_mycourse_url()
    chapter_detail = get_chapter_url(course_url)
    watch_video_and_do_homework(chapter_detail)
    logout()

if __name__ == '__main__':

    engine()
