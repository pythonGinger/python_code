#-*-coding:utf-8-*-
from bs4 import BeautifulSoup as BS
import urllib, urllib2, cookielib
from getpass import getpass
from random import randint
from PIL import Image
import hashlib
import json
import time
import ssl
import re

domain = 'https://mooc1-2.chaoxing.com'
headers = {
'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0',
'Referer':'http%3A%2F%2Fi.mooc.chaoxing.com',
}
ssl._create_default_https_context = ssl._create_unverified_context
cookiejar = cookielib.CookieJar()
urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))# container save cookie

def greeting():

    print '\n'
    print '----------' * 5
    print 'Welcome! I am Mr.robot !'
    print 'Warning !!!'
    print 'I wrote the tool just for fun !'
    print 'Prohibition for commercial use !'
    print 'If you catch any question!'
    print 'Please contact Mr.robot!'
    print 'For security !'
    print 'The password is invisible !'
    print '----------' * 5
    print '\n'

def login():

    while True:
        login_url = 'http://passport2.chaoxing.com/login?refer=http://i.mooc.chaoxing.com'
        vcode_url = 'http://passport2.chaoxing.com/num/code'
        req = urllib2.Request(login_url, headers=headers)
        res = urlOpener.open(req)
        img_content = urlOpener.open(vcode_url).read()
        print '----------' * 5
        u = raw_input('Username: ')
        p = getpass('Password: ')
        with open ('vcode.jpeg', 'wb') as f:
            f.write(img_content)
        Image.open('vcode.jpeg').show()
        vcode = raw_input('Vcode: ')
        form = {
        'uname':u,
    	'password': p,
    	'numcode':vcode,
        'isCheckNumCode':1,
        'refer_0x001':'http%3A%2F%2Fi.mooc.chaoxing.com',
        'fidName':'上海市大学生安全教育在线',
        'productid':None,# unnecessary parameter
    	'pidName':None,  # unnecessary parameter
        'verCode':None,  # unnecessary parameter
        'allowJoin':0,   # unnecessary parameter
    	'fid':'21383',
        'pid':-1,
    	'f':0,
        }
        data = urllib.urlencode(form) #encode form parameters
        req1 = urllib2.Request(login_url, headers=headers, data=data)
        html = urlOpener.open(req1).read() # login then get the passport
        if 'settings/info' in html:
            print 'Login successfully !'
            print '----------' * 5
            break
        else:
            print 'Please check your username, password and vcode !\nMake sure you enter them right !'

def get_mycourse():

    mycourse_page = 'http://mooc1-2.chaoxing.com/visit/courses' # the page contain courses' info
    mycourse_request = urllib2.Request(mycourse_page, headers=headers)
    mycourse_response = urlOpener.open(mycourse_request).read()
    mycourse_pat = r'/mycourse/studentcourse+.+courseId=\d{9}&clazzid=\d{7}&enc=\w{32}' # the specific num can be changed
    mycourse = re.findall(mycourse_pat, mycourse_response)[0] # at present I have only one course
    course_url = domain + mycourse
    return course_url

def get_chapter(course_url):

    course_request = urllib2.Request(course_url, headers=headers) # the page contain the chapter info
    course_response = urlOpener.open(course_request).read()
    soup = BS(course_response, 'html.parser')
    chapter_detail = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if len(href) == 114:
            clazzid = href[70:77]
            courseid = href[52:61]
            chapterid = href[33:42]
            #enc = href[82:]
            chapter_detail.append((clazzid, courseid, chapterid))
            #print(clazzid, courseid, chapterid)
    return chapter_detail
    #There are many noise in the page for the reason why I choose BeautifulSoup instead of re to match the href

def get_video_question(chapter_detail):

    #knowledgeid is same as chapterId
    #video detail in the page when num=0 or num=1
    #question detail in the next page
    #for detail in chapter_detail:
    clazzid, courseid, knowledgeid = chapter_detail[1]
    for num in range(2):
        video_url = domain + '/knowledge/cards?clazzid=%s&courseid=%s&knowledgeid=%s&num=%d&v=20160407-1' % (clazzid, courseid, knowledgeid, num)
        video_request = urllib2.Request(video_url, headers=headers)
        video_response = urlOpener.open(video_request).read()
        soup = BS(video_response, 'html.parser')
        if len(soup.title.get_text()) == 2:
            #callback = cheat(video_response)
            #if callback == 'success':
                #break
            scrapy_question(clazzid, courseid, knowledgeid, num)
            break
        time.sleep(2)
    delay = randint(3,5)
    time.sleep(delay)#warning: the server will detect the interval time
    print '---------' * 5
    print 'The server will detect the interval time!\nFor security!\nPlease wait %s seconds!' % delay
    print '---------' * 5

def scrapy_question(clazzid, courseid, knowledgeid, num):

    question_url = domain + '/knowledge/cards?clazzid=%s&courseid=%s&knowledgeid=%s&num=%d&v=20160407-1' % (clazzid, courseid, knowledgeid, num+1)
    request = urllib2.Request(question_url, headers=headers)
    response = urlOpener.open(request).read()
    info_json = match_info(response)
    workId = info_json['attachments'][0]['property']['workid']
    jobid = info_json['attachments'][0]['property']['jobid']
    courseId = info_json['defaults']['courseid']
    userid = info_json['defaults']['userid']
    classId = info_json['defaults']['clazzId']
    knowledgeid = info_json['defaults']['knowledgeid']
    enc = info_json['attachments'][0]['enc']
    q_url = domain+'/workHandle/handle?workId=%s&courseid=%s&knowledgeid=%s&userid=%s&ut=s&classId=%s&jobid=%s&type=&isphone=false&submit=false&enc=%s&utenc=9cb1efcfb2c60e398c133b5bc067a9af' % (workId, courseId, knowledgeid, userid, classId, jobid, enc)
    q_req = urllib2.Request(q_url, headers=headers)
    q_rep = urlOpener.open(q_req).read()
    action_p = r'addStudentWorkNewWeb+.+_classId=\d{7}&courseid=\d{9}&token=\w{32}&totalQuestionNum=\w{32}'
    actions = re.findall(action_p, q_rep)
    if actions:
        form_action = domain + '/' + actions[0]

    soup = BS(q_rep, 'html.parser')
    for inp in soup.find_all('input'):
        if inp['type'] == 'radio':
            print inp['name'], inp['value']
    for link in soup.find_all('a'):
        print link.get_text()
    for div in soup.find_all('div'):
        if div.has_attr('style') and not div.has_attr('id'):
            print div.get_text()

def match_info(response):

    pattern = r'{"attachments"+.+"control":true}'
    batch = re.findall(pattern, response)[0]
    return json.loads(batch)
    #print json.dumps(json.loads(batch), sort_keys=True, indent=4, separators=(',', ':'))
    #for debug and find the important info I make the info_json more pretty

def cheat(video_response):

    info_json = match_info(video_response)
    otherInfo = info_json['attachments'][0]['otherInfo']
    objectId = info_json['attachments'][0]['objectId']
    jobid = info_json['attachments'][0]['jobid']
    userid = info_json['defaults']['userid']
    clazzId = info_json['defaults']['clazzId']
    duration, dtoken = get_duration_dtoken(objectId)
    clipTime, playingTime, enc = crypto(clazzId, userid, jobid, objectId, duration)
    callback = report(dtoken, otherInfo, userid, jobid, clipTime, objectId, clazzId, duration, playingTime, enc)
    return callback

def get_duration_dtoken(objectId):

    status_url = 'https://mooc1-2.chaoxing.com/ananas/status/' + objectId
    request = urllib2.Request(status_url, headers=headers)
    response = urlOpener.open(request).read()
    json_rep = json.loads(response)
    duration = json_rep['duration']
    dtoken = json_rep['dtoken']
    return duration, dtoken

def crypto(clazzId, userid, jobid, objectId, duration):

    playingTime = int(duration) - 1
    salt = 'd_yHJ!$pdA~5'
    clipTime = '0_' + str(playingTime)
    crypto_method = "[{}][{}][{}][{}][{}][{}][{}][{}]".format(clazzId, userid, jobid, objectId, playingTime*1000, salt, duration*1000, clipTime)
    md = hashlib.md5()
    md.update(crypto_method.encode('utf-8'))
    enc = md.hexdigest()
    return clipTime, playingTime, enc

def report(dtoken, otherInfo, userid, jobid, clipTime, objectId, clazzId, duration, playingTime, enc):

    play_report_url = """
    https://mooc1-2.chaoxing.com/multimedia/log/%s?otherInfo=%s&userid=%s&rt=0.9&jobid=%s&clipTime=%s&dtype=Video&objectId=%s&clazzId=%s&duration=%s&view=pc&playingTime=%s&isdrag=3&enc=%s
    """ % (dtoken, otherInfo, userid, jobid, clipTime, objectId, clazzId, duration, playingTime, enc)
    request = urllib2.Request(play_report_url, headers=headers)
    response = urlOpener.open(request).read()
    if 'true' in response:
        print '^_^ Chapter %s is passed! ^_^\n' % otherInfo
        return 'success'
    else:
        print '>_< Sorry the robot is tired! >_<\n'
        return 'fail'

def logout():

    out_url = 'https://passport2.chaoxing.com/logout.html?'
    out_req = urllib2.Request(out_url, headers=headers)
    out_rep = urlOpener.open(out_url).read()

def engine():

    greeting()
    login()
    course_url = get_mycourse()
    chapter_detail = get_chapter(course_url)
    get_video_question(chapter_detail)
    logout()

if __name__ == '__main__':

    engine()
