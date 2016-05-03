#!/usr/bin/python
# coding=utf-8
import sys
import time
import sqlite3
import telepot
from pprint import pprint
from datetime import date, datetime
from urllib2 import Request, urlopen
from urllib import urlencode, quote_plus
from bs4 import BeautifulSoup
import re
import traceback

key = 'mcGA6xDEsvdIH3sbow%2B7gIBwxcGJC4dTkHt%2Bd7DXJ2pg2Gqq3g6IvU%2BLwFKCiqOQncYX2uI2Kav1yzRw7WO1RA%3D%3D'
url = 'http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptRent?ServiceKey='+key

#텔레그램 상으로는 4096까지 지원함. 가독성상 1000정도로 끊자.
MAX_MSG_LENGTH = 1000


def sendMessage(id, msg):
    try:
        bot.sendMessage(id, msg)
    except:
        print str(datetime.now()).split('.')[0]
        traceback.print_exc(file=sys.stdout)

def help(id):
    sendMessage(id, '''아파트 전월세 정보 알림용 텔레그램 봇입니다.
명령어 사용법:
/howmuch 지역코드 년월 필터 : 해당 지역의 월 거래를 확인하며, 필터를 포함하는 정보를 조회합니다.
 (년월이 생략되면 현재 월로 설정되며, 필터가 생략되면 전체 구/군의 정보가 나옵니다.)
 ex. /howmuch 11710 201603
 ex. /howmuch 11710
 ex. /howmuch 11710 201603 잠실
/loc 지역명 : 지역코드 검색.
 ex. /loc 송파
/noti add 지역코드 필터 : 노티 등록. howmuch의 사용법과 유사하며, 해당 결과가 있을 경우 매일 아침에 전송함(필터생략가능. 첫 노티는 전월 데이터도 전송됩니다).
 ex. /noti add 11710 잠실
/noti list : 노티 리스트 조회.
/noti remove 아이디 : 노티 제거.

자매품>
@apart_bot : 아파트 매매 봇
@officetel_bot : 연립/다세대 매매 봇
@house_meme_bot : 단독/다가구 매매 봇
@aptrent_bot : 아파트 전월세 봇
''')

def howmuch(loc_param, date_param, filter_param):
    res_list = []
    res=''
    printed = False
    request = Request(url+'&LAWD_CD='+loc_param+'&DEAL_YMD='+date_param)
    request.get_method = lambda: 'GET'
    try:
        res_body = urlopen(request).read()
    except UnicodeEncodeError:
        res = ['오류가 발생했습니다. 명령어를 정확히 사용했는지 확인해 보세요.']
        return res
    soup = BeautifulSoup(res_body, 'html.parser')
    items = soup.findAll('item')
    rTuple = re.compile('<(.*?)>([^<]+)')

    for item in items:
        try:
            item = item.text.encode('utf-8')
            #print item
            office={}
            for tuples in rTuple.findall(item):
                office[tuples[0]] = tuples[1].strip()
                #print "\t", tuples[0], tuples[1]
            #row = parsed[2]+'/'+parsed[6]+'/'+parsed[7]+', '+parsed[4]+parsed[9]+' '+parsed[5]+', '+parsed[8]+'m², '+parsed[10]+'F, '+parsed[1].strip()+'만원\n'
            row=''
            #wolse=''
            #if office['월세금액']!='0':
            wolse=', 월세:'+office['월세금액']+'만원'
            row += office['년']+'/'+office['월']+'/'+office['일']+', '+office['법정동']+' '+office['지번']+', '+office['아파트']+' '+office['층']+'F, '+office['전용면적']+'m², 전세:'+office['보증금액']+'만원'+wolse+'\n'
        except:
            print str(datetime.now()).split('.')[0]
            traceback.print_exc(file=sys.stdout)

        if filter_param and row.find(filter_param)<0:
            row = ''
        #print row
        if len(res+row)>MAX_MSG_LENGTH: # becuz of telegram max msg length restrict
            res_list.append(res)
            res=row
            printed = True
        else:
            res+=row
    if res:
        res_list.append(res)
    elif not printed:
        res_list = ['조회 결과가 없습니다.']
    return res_list

def noti(command, subparam, user):
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS user(id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, command TEXT)')

    if command=='add':
        if not subparam:
            return False
        try:
            c.execute('INSERT INTO user (user,command) VALUES ("%s", "%s")'%(user, subparam))
            conn.commit()
        except:
            sendMessage(user, 'DB에러가 발생했습니다. 명렁어에 에러가 있나 살펴보시거나 잠시 후에 사용해 주세요.')
        else:
            sendMessage(user, '성공적으로 추가되었습니다. /noti list로 확인 가능합니다.')
        return True
    if command=='list':
        res=''
        printed = False
        c.execute('SELECT * from user WHERE user="%s"'%user)
        for data in c.fetchall():
            row = 'id:'+str(data[0])+', command:'+data[2]+'\n'
            if len(row+res)>MAX_MSG_LENGTH:
                sendMessage(user, res)
                res=row
                printed = True
            else:
                res+=row
        if res:
            sendMessage(user, res)
        elif not printed:
            sendMessage(user, '조회 결과가 없습니다.')
        return True
    if command=='remove':
        if not subparam:
            return False
        try:
            c.execute('DELETE FROM user WHERE user="%s" AND id=%s'%(user, subparam))
            conn.commit()
        except:
            sendMessage(user, 'DB에러가 발생했습니다. 명렁어에 에러가 있나 살펴보시거나 잠시 후에 사용해 주세요.')
        else:
            sendMessage(user, '성공적으로 제거되었습니다. /noti list로 확인 가능합니다.')
        return True
    if command=='all':
        res=''
        printed = False
        c.execute('SELECT * from user')
        for data in c.fetchall():
            row = 'id:'+str(data[0])+',user:'+data[1]+',command:'+data[2]+'\n'
            if len(row+res)>MAX_MSG_LENGTH:
                sendMessage(user, res)
                res=row
                printed = True
            else:
                res+=row
        if res:
            sendMessage(user, res)
        elif not printed:
            sendMessage(user, '조회 결과가 없습니다.')
        return True
    return False

def handle(msg):
    conn = sqlite3.connect('loc.db')
    c = conn.cursor()

    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type != 'text':
        sendMessage(chat_id, '난 텍스트 이외의 메시지는 처리하지 못해요.')
        return
    #pprint(msg)

    text = msg['text']
    args = text.split(' ')
    res = ''
    if text.startswith('/'):
        if text.startswith('/loc'):
            if len(args)>1:
                param = args[1]
                c.execute('SELECT * FROM location WHERE loc LIKE "%%%s%%"'%param)
                for data in c.fetchall():
                    res += data[0] + ' : ' + data[1] + '\n'
                if not res:
                    res = '조회 결과가 없습니다. 구/군 이름으로 검색해 보세요.'
                sendMessage(chat_id, res)
                return

        if text.startswith('/howmuch'):
            if len(args)>1:
                loc_param = args[1]
                if len(args)>2:
                    date_param = args[2]
                else:
                    today = date.today()
                    date_param = today.strftime('%Y%m')
                filter_param=''
                if len(args)>3:
                    filter_param = args[3].encode('utf-8')
                res_list = howmuch( loc_param, date_param, filter_param )
                for res in res_list:
                    sendMessage(chat_id, res)
                return

        if text.startswith('/noti'):
            if len(args)>1:
                command = args[1]
                subparam = text.split(command)[1].strip()
                res = noti(command, subparam, chat_id)
                if res:
                    return

    help(chat_id)

TOKEN = sys.argv[1]
print 'received token :', TOKEN

bot = telepot.Bot(TOKEN)
pprint( bot.getMe() )

bot.notifyOnMessage(handle)

print 'Listening...'

while 1:
  time.sleep(10)