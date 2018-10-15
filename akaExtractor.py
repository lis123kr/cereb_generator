# Copyright 2018 Cerebro Scholar
# generated by JE KIM
# 2018. 10. 15
"""
keylist로부터 AKA를 추출. 
괄호에서 AKA후보들을 추출하고, 가장 많이 등장한 형태를 AKA의 대표값으로 지정함.(임시방편)

return 형태
{'aami': 'associ for advanc of medic instrument',
 'aann': 'autoassoci neural network',
 'abc': 'artifici bee coloni algorithm',
 'abnid': 'anomali base network intrus detect',
 'ac': 'air condit',
 'acds': 'adapt critic design',...}
"""
import re
import pandas as pd
from generateTagset import * 

def findMax(x) :
    """가장 많이 등장한 형태를 AKA와 매칭 (임시)"""
    return pd.Series(x).value_counts().sort_values(ascending=False).index[0]

def tuning(akaDict) :
    """괄호안에 있지만 축약형이 아닌 경우가 있음. ex. machine learning(linear) """
    del akaDict['linear']

    return akaDict

def aka_extractor(keylist) :
    """Find out AKA from corpus"""
    key_series = pd.Series(keylist)

    aka = pd.DataFrame()

    aka['long']=key_series.str.extract(r'(.+)(\(.+?\))').iloc[:,0]
    aka['short']=key_series.str.extract(r'(.+)(\(.+?\))').iloc[:,1]

    aka = aka[aka.short.notnull()]
    aka['short'] = aka.short.apply(lambda x : x[1:-1])

    cond_swap = aka.apply(lambda x: len(x.long) < len(x.short), axis=1)

    temp = aka[cond_swap].long
    aka.long[cond_swap] = aka.short
    aka.short[cond_swap] = temp

    aka.short = aka.short.apply(lambda x : x.strip())
    aka.long = aka.long.apply(lambda x : x.strip())

    aka.drop_duplicates(['long','short'], inplace=True)
    aka['stem'] = aka.long.apply(tokenize_and_stem_and_connect)

    akag= aka.groupby('short').agg({'stem' : lambda x : list(x)})
    akag['most']= akag.stem.apply(lambda x: findMax(x))


    akaDict = tuning(akag['most'].T.to_dict())

    return akaDict