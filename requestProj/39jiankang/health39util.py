#!/usr/bin/python
# encoding: utf-8

#主要是对爬取39健康网的相关方法的封装相关操作的封装
import requests
from pyquery import PyQuery as pq

class health39util(object):
    def __init__(self):
        pass

    def parse_disease(self, url):
        '''
        解析疾病页面
        '''
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36 Maxthon/5.2.1.6000'}
        html = requests.get(url,headers=headers)
        html.encoding = 'gbk'
        d = pq(html.text)
        #疾病名称
        name = d('div.spreadhead > div.tit.clearfix > a > h1').eq(0).text()
        intro = d('dl.intro > dd').eq(0).text()
        if intro.endswith('详细>>'):
            intro = intro[:-4]
        dds = d('div.info > ul > li')
        dict1 = dict()
        dict1['url'] = url
        dict1['疾病名称'] = name
        dict1['简介'] = intro
        for i in range(len(dds)):
            label = dds.eq(i)('i').eq(0).text()
            s = dds.eq(i).text()    
            if s.endswith('[详细]'):
                s = s[:-4].strip()
            ss = [i.strip() for i in s.split('：')]
            content = dds.eq(i)('a')
            if content and ss[0] in ['典型症状','临床检查','并发症','手术','常用药品']:
                ll = list()
                for ii in range(len(content)):
                    if content.eq(ii).attr.title:
                        ll.append(content.eq(ii).attr.title)
                dict1[ss[0]] = ll
            else:
                dict1[ss[0]] = ss[1]
        drug = d('.drug > ul >li').eq(0)
        if drug:
            aa = drug('a')
            if aa:
                ll = list()
                for i in range(len(aa)):
                    if aa.get(i).attr.title:
                        ll.append(aa.get(i).attr.title)
                dict1[drug('i').text()[:-1]] = ll
        return dict1