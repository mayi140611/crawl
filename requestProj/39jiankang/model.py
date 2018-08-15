import sys
sys.path.append('/home/ian/code/github')
import gensim
import jieba
import numpy as np
import pandas as pd
from scipy.linalg import norm
from utils.pickle_wrapper import pickle_wrapper as pkw
from utils.nlp.nlp_wrapper import nlp_wrapper as nlpw
from utils.pandas_wrapper import pandas_wrapper as pdw
from utils.nlp.nlp_wrapper import nlp_wrapper as nlpw
import re

class model_wrapper(object):
    def __init__(self):        
        self._model_file = '/home/ian/code/github/data/word2vec/news_12g_baidubaike_20g_novel_90g_embedding_64.bin'
        self._model = gensim.models.KeyedVectors.load_word2vec_format(self._model_file, binary=True)
        self._zzlist = self.get_zzlist()
        self._zzshared_series = pkw.loadfromfile('共有症状Series.pkl')
        self._zzshared_series_inv = pkw.loadfromfile('共有症状逆序Series.pkl')
        self._tongxianmatr = pkw.loadfromfile('同现矩阵ndarray.pkl')
    def get_zzlist(self,filepath=None):
        '''
        获取症状列表
        '''
        if not filepath:
            filepath = '症状列表.pkl'
        # from utils.pymongo_wrapper import pymongo_wrapper as pmw

        # client = pmw()

        # zztable = client.get_collection('jiankang39', 'zz')

        # zzlist = [i['症状名称'] for i in client.find_all(zztable, fieldlist=['症状名称'])]



        # from utils.pickle_wrapper import pickle_wrapper as picklew

        # picklew.dump2file(zzlist,'症状列表.pkl')
        zzlist = pkw.loadfromfile(filepath)
        print(len(zzlist),zzlist[:5])
        return zzlist
    
    def get_zzs_by_editdis(self,s1,zzlist=None, n=3): 
        '''
        通过编辑距离计算相似度
        '''
        if not zzlist:
            zzlist = self._zzlist
        e = list(map(nlpw.cal_editdistance, [s1]*len(zzlist), zzlist))
        df = pdw.build_df_with_dict({'zz':zzlist,'e':e})
        return list(pdw.sort_by_column(df,'e').loc[:,'zz'][:n].values)
    def get_zzs_by_word2vec(self,s1,zzlist=None,n=2):
        '''
        通过word2vec模糊推荐症状
        '''
        if not zzlist:
            zzlist = self._zzlist
        def vector_similarity(s1, s2):
            def sentence_vector(s):
                words = jieba.lcut(s)
                v = np.zeros(64)
                for word in words:
                    if word in self._model:
                        v += self._model[word]
                v /= len(words)
                return v
            try:
                v1, v2 = sentence_vector(s1), sentence_vector(s2)
                return np.dot(v1, v2) / (norm(v1) * norm(v2))
            except:
                return 0            
        e = list(map(vector_similarity, [s1]*len(zzlist), zzlist))
        df = pdw.build_df_with_dict({'zz':zzlist,'e':e})
        return list(pdw.sort_by_column(df,'e',ascending=False).loc[:,'zz'][:n].values)
    def get_zzs(self,s1,zzlist=None,n1=2,n2=3):
        if not zzlist:
            zzlist = self._zzlist
        s1 = re.sub(r'[我你他很的了么吗呢也啊特,，。]|(感觉)|(有点)|(非常)|(特别)','',s1)
        s1 = re.sub(r'胳膊','上臂上肢前臂',s1)
        s1 = re.sub(r'小腿','小腿下肢',s1)
        s1 = re.sub(r'大腿','大腿下肢',s1)
        s1 = re.sub(r'脸','脸面部',s1)
        s1 = re.sub(r'喉咙','喉咙咽喉',s1)
        s1 = re.sub(r'嘴','嘴口',s1)
    #     s1 = re.sub(r'牙','牙牙齿',s1)
        s1 = re.sub(r'屁股','屁股臀部',s1)
        s1 = re.sub(r'肚子','肚子腹部',s1)
        s1 = re.sub(r'脚','脚足',s1)
    #     s1 = re.sub(r'[疼痛]','疼痛',s1)
        print(s1)
        if s1 in zzlist:
            return s1
        return list(set(self.get_zzs_by_word2vec(s1,zzlist,n1)+self.get_zzs_by_editdis(s1,zzlist,n2)))

    def zz2zz(self,zzlist1):
        t = [self._zzshared_series_inv[i] for i in zzlist1 if i in self._zzshared_series_inv]
        if t:
            r = None
            for i in t:
                if not r:
                    r = self._tongxianmatr[i]
                else:
                    r = r + self._tongxianmatr[i]
                s = pd.Series(list(r)).sort_values(ascending=False)
                l = list(s[s>0].index)
                l1 = [i for i in l if i not in t]
                if l1:
                    z = [self._zzshared_series[i] for i in l1]
                    return z,[s[i] for i in l1]