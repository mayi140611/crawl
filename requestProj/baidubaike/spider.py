#!/usr/bin/python
# encoding: utf-8

"""
@author: Ian
@contact:luoyonggui@wondersgroup.com
@file: spider.py
@time: 2018/4/9 16:56
"""
import pickle
import pymongo
import requests
from multiprocessing import Pool
from pyquery import PyQuery as pq
from requests.exceptions import ConnectionError

from baidubaike.config import *

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]
dict1 = dict()
dict1['symptoms'] = 75953 # 疾病症状
dict1['medicine'] = 75954 #药物
dict1['medicineCh'] = 75956 #中医药
dict1['dtmethod'] = 75955 #Diagnosis and treatment method 诊疗方法


def get_index(list1):
    '''
    获取dict1中的链接
    :param page:
    :param tagId:
    :param mongodoc: mongodb表名
    :return:
    '''
    page, tagId, mongodoc = list1[0],list1[1],list1[2]
    data = {
        'limit':24,
        'timeout':3000,
        'filterTags':[],
        'tagId':tagId,
        'fromLemma':'false',
        'contentLength':40,
        'page':page,
    }
    url = 'https://baike.baidu.com/wikitag/api/getlemmas'
    headers = {
        'User-Agent': 'Mozilla / 5.0(Windows NT 6.1;\
            WOW64) AppleWebKit / 537.36(KHTML, like\
            Gecko) Chrome / 55.0\
            .2883\
            .75\
            Safari / 537.36\
            Maxthon / 5.1\
            .3\
            .2000'
    }

    try:
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            totalpage = response.json()['totalPage']
            list1 = response.json()['lemmaList']
            print('{}{}'.format(mongodoc, response.json()['page']))
            db[mongodoc].insert_many(list1)
            return totalpage
        return None
    except ConnectionError:
        print('Error occurred')
        return None

# proxy = None

#
# def get_proxy():
#     try:
#         response = requests.get(PROXY_POOL_URL)
#         if response.status_code == 200:
#             return response.text
#         return None
#     except ConnectionError:
#         return None


def get_detail(list1, count=1, count2=0):
    url = list1[0]
    key = list1[1]
    headers = {
        'User-Agent': 'Mozilla / 5.0(Windows NT 6.1;\
                WOW64) AppleWebKit / 537.36(KHTML, like\
                Gecko) Chrome / 55.0\
                .2883\
                .75\
                Safari / 537.36\
                Maxthon / 5.1\
                .3\
                .2000',
         }
    try:
        if count >= MAX_COUNT:
            print('Tried Too Many Counts')
            return None
        # if proxy:
        #     proxies = {
        #         'http': 'http://' + proxy,
        #         'https': 'http://' + proxy,
        #     }
        #     response = requests.get(url, allow_redirects=False, headers=headers, proxies=proxies)
        # else:
        response = requests.get(url, allow_redirects=False, headers=headers)
        print('{}@@@@@{}'.format(url, response.status_code))
        if response.status_code == 200:
            response.encoding = 'utf-8'
            doc = pq(response.text)
            title = doc('.lemmaWgt-lemmaTitle-title > h1').text()
            abstract = doc('div.para:nth-child(1)').text()
            basicInfoList = doc('dl.basicInfo-block')
            dict2 = {}
            dict2['title'] = title  # 名称
            dict2['abstract'] = abstract  # 摘要
            dict2['url'] = url
            # 基本信息列表
            for t in range(len(basicInfoList)):
                dds = basicInfoList.eq(t).find('dd')
                dts = basicInfoList.eq(t).find('dt')
                for i in range(len(dds)):
                    dict2['dd{}'.format(dts.eq(i).text())] = dds.eq(i).text()

            divs = doc('div.main_tab > div')
            if len(divs) == 0:
                divs = doc('div.main-content > div')

            # sectionList
            name = ''
            for i in range(len(divs)):
                if divs.eq(i).attr('class') == 'anchor-list':
                    name = divs.eq(i)('a:nth-child(3)').attr('name')
                    if name:
                        name = name.replace('.', '_')  # InvalidDocument: key '3.病原学' must not contain '.'
                        dict2[name] = ''
                elif divs.eq(i).attr('class') == 'para':
                    if name in dict2:
                        if dict2[name] == '':
                            dict2[name] = divs.eq(i).text()
                        else:
                            dict2[name] = '{}\n{} '.format(dict2[name], divs.eq(i).text())
            return dict2
        else:
            print(response.status_code)
            # Need Proxy
            if count2 < 15:
                proxy = get_proxy()
                count2 += 1
            else:
                proxy = None#尝试15次代理仍不成功的话，尝试一下本机ip是否已经解封
                return get_detail(list1)

            if proxy:
                print('{}Using Proxy{}'.format(count2, proxy))
                return get_detail(list1, count2=count2)
            else:
                print('Get Proxy Failed')
                global errorList
                errorList.append('{},{}'.format(key, url))
                return None
    except ConnectionError as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        count += 1
        return get_detail(list1, count, count2)


def get_detail1(list1):
    url = list1[0]
    key = list1[1]

    headers = {
        'User-Agent': 'Mozilla / 5.0(Windows NT 6.1;\
                WOW64) AppleWebKit / 537.36(KHTML, like\
                Gecko) Chrome / 55.0\
                .2883\
                .75\
                Safari / 537.36\
                Maxthon / 5.1\
                .3\
                .2000',
       }
    try:
        response = requests.get(url, allow_redirects=False, headers=headers)
        print('{}{}@@@@@{}'.format(key, url, response.status_code))
        if response.status_code == 200:
            response.encoding = 'utf-8'
            doc = pq(response.text)
            dict2 = dict()
            authority1 = doc('.authorityListPrompt > div')
            if len(authority1) > 0:
                authority = authority1.text()
                dict2['authority'] = authority # 信息来源
            title = doc('.lemmaWgt-lemmaTitle-title > h1').text()
            abstract = doc('div.para:nth-child(1)').text()
            basicInfoList = doc('dl.basicInfo-block')
            dict2['title'] = title  # 名称
            dict2['abstract'] = abstract  # 摘要
            dict2['url'] = url
            # 基本信息列表
            for t in range(len(basicInfoList)):
                dds = basicInfoList.eq(t).find('dd')
                dts = basicInfoList.eq(t).find('dt')
                for i in range(len(dds)):
                    dict2['dd{}'.format(dts.eq(i).text())] = dds.eq(i).text()

            divs = doc('div.main_tab > div')
            if len(divs) == 0:
                divs = doc('div.main-content > div')

            # sectionList
            name = ''
            for i in range(len(divs)):
                if divs.eq(i).attr('class') == 'anchor-list':
                    name = divs.eq(i)('a:nth-child(3)').attr('name')
                    if name:
                        name = name.replace('.', '_')  # InvalidDocument: key '3.病原学' must not contain '.'
                        dict2[name] = ''
                elif divs.eq(i).attr('class') == 'para':
                    if name in dict2:
                        if dict2[name] == '':
                            dict2[name] = divs.eq(i).text()
                        else:
                            dict2[name] = '{}\n{} '.format(dict2[name], divs.eq(i).text())
            return dict2
        else:
            return 302
    except ConnectionError as e:
        return None


def get_all_indexes():
    '''

    :return:
    '''
    pool = Pool(processes=4)
    for k, v in dict1.items():
        totalpage = get_index([0, v, k])
        pool.map(get_index, [[p, v, k] for p in range(1, totalpage)])
        # page = 1
        # while(page < totalpage):
        #     page += 1
        #     get_index(page, v, k)
        #     print(page)
    pool.close()
    pool.join()


def parse_detail():
    errorlist = []  # 存储爬取失败的链接
    for k, v in dict1.items():
        connection = db[k]
        print('-----------------------------------{}-----------------------------------'.format(k))
        count = 0
        for t in connection.find({"status__": {'$ne': "done"}},
                no_cursor_timeout = True):  # pymongo.errors.CursorNotFound: Cursor not found, cursor id: 124891571478
            item = get_detail1([t['lemmaUrl'].replace('http', 'https', 1), k])
            if item:
                if item == 302:
                    errorlist.append(t['lemmaUrl'].replace('http', 'https', 1))
                    continue
                db['{}detail'.format(k)].insert_one(item)
                connection.update_one({'_id': t.get('_id')}, {'$set': {'status__': 'done'}})
                count += 1
            else:
                print(count)
                break
    print(len(errorlist))
    if errorlist:
        with open('pt.pkl', 'wb') as f:
            pickle.dump(errorlist, f)

if __name__ == '__main__':
    #第一步，获取所有的网址链接
    #get_all_indexes()
    #第二步，解析每个页面
    parse_detail()

    print('done!')
