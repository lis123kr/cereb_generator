# Copyright 2018 Cerebro Scholar
# generated by JE KIM
# 2018. 10. 15
"""
generate TagDict from keylist

tagDict : dataframe of tags [tag, stemmed, rawkeys, keyDetected]
rawToTag : dataframe of rawkey and matching tag. [rawkey, tag]
"""
import pandas as pd
from printUtils import *
import nltk
# load nltk's SnowballStemmer as variabled 'stemmer'
from nltk.stem.snowball import SnowballStemmer
import re

stemmer = SnowballStemmer("english")

def tokenize_and_stem_and_connect(text):
    """tokenizing for stemming and processing '-' also."""
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    # print(text,'\n==> after tokenize :', tokens)
    tokens_add = sum(list(map(lambda x:x.split('-'), tokens)),[])
    # print(tokens,'\n==> after tokenize with - :', tokens_add)
    stems = [stemmer.stem(t) for t in tokens_add]
    # print('==> stemmed :', stems)
    connect = " ".join(stems)
    # print('==> connect :', connect)

    return connect

def step1_stem_compare(keylist) :
    print(yellow('Step1. Stem and compare.'))
    
    unique = pd.Series(keylist).value_counts()

    uni_keys = pd.Series(unique.index)
    uni_counts = pd.Series(unique.values)
    stemmed_keys = uni_keys.apply(lambda x: tokenize_and_stem_and_connect(x))

    group = pd.DataFrame({
        'rawkeys' : uni_keys,
        'stemmed' : stemmed_keys,
        'keyDetected' : uni_counts
    }).groupby('stemmed')

    tagDict = group.agg({
        'rawkeys' : lambda x: list(x),
        'keyDetected' : 'sum'
    }).sort_values(by='keyDetected', ascending=False)

    tagDict['tag'] = group.apply(lambda x : x.sort_values(by='keyDetected', ascending = False)['rawkeys'].tolist()[0])
    tagDict.reset_index(inplace=True)

    tagDict.stemmed = tagDict.stemmed.apply(lambda x : [x])

    print(yellow('Done. {:,} unique rawkeys are clustered to {:,} tags').format(len(uni_keys), len(tagDict)))

    return tagDict

def step2_aka_compare(tagDict, akaDict) :
    print(yellow('Step2. AKA compare.'))
    cnt = [0]
    for aka,stem in akaDict.items() :
         combine(tagDict, aka, stem, cnt)

    print('total {:,} AKA combined with existing group.'.format(cnt[0]))

    return tagDict

def step3_bracket_compare(tagDict) :
    """"일단 괄호안 무시."""
    print(yellow('Step3. bracket compare.'))

    # 같이 묶고 싶은 줄의 newgroup값을 0으로    
    cnt = [0]
    bracket_td = tagDict[tagDict.tag.apply(lambda x :re.compile('[(].+?[)]').search(x) != None)] 
    bracket_td.apply(lambda x: combine(tagDict, tokenize_and_stem_and_connect(x.tag), re.sub(r'[(].+?[)]','', tokenize_and_stem_and_connect(x.tag)).strip(), cnt), axis=1)

    print('total {:,} bracket removed & combine with existing group.'.format(cnt[0]))

    return tagDict


def combine(tagDict, a,b, cnt=[0]) :
    # stemmed a와 stemmed b가 들어있는 각 그룹을 합침.
    data_a = tagDict[tagDict.stemmed.apply(lambda x : a in x)]
    data_b = tagDict[tagDict.stemmed.apply(lambda x : b in x)]

    if len(data_a) == 0 or len(data_b) == 0: 
        return
    
    if data_a['keyDetected'].values[0] > data_b['keyDetected'].values[0] :
        i = data_a.index.values[0]
        j =  data_b.index.values[0]
    else :
        i = data_b.index.values[0]
        j =  data_a.index.values[0]
        
    if i==j : return

    # print('combine', a,b)
        
#     j -> i & drop j
    tagDict.at[i,'stemmed'] = data_a.stemmed.values[0] + data_b.stemmed.values[0]
    tagDict.at[i,'rawkeys'] = data_a.rawkeys.values[0] + data_b.rawkeys.values[0]
    tagDict.at[i,'keyDetected'] = data_a.keyDetected.values[0] + data_b.keyDetected.values[0]
    
    tagDict.drop(j, inplace=True)
#     print('yes')

    cnt[0] = cnt[0] + 1
    # if a == 'ml'  :
    #     print(len(data_a), len(data_b))
    #     print(data_a)
    #     print(data_b)
    #     print(tagDict[tagDict.tag=='machine learning'])


def genTagDict(keylist=None, akaDict=None) :
    print(blue('\n=> Generating tagDict...'))
    if keylist is None :
        print('TODO : get keylist from cerebDB directly')
        return
    
    tagDict = step1_stem_compare(keylist)
    if akaDict != None : step2_aka_compare(tagDict, akaDict)
    step3_bracket_compare(tagDict)

    tagDict.set_index('tag', inplace=True)

    print(blue('TagDict: Success. From {:,} rawkeys, unique {:,} tags are generated.'.format(len(keylist), len(tagDict))))
    # print(df_rawkeys.key.value_counts())
    print(tagDict)

    return tagDict


def spreading(x, rawToTag) :
    for each in x.rawkeys :
        rawToTag.append({'rawkey' : each, 'tag' : x.tag })


def genRawToTag(tagDict) :
    print(blue('\n=> Generating RawToTag...'))

    dictTemp = tagDict.reset_index()
    rawToTag = []

    dictTemp.apply(lambda x:spreading(x, rawToTag), axis=1)
    df_rawToTag = pd.DataFrame(rawToTag, columns=['rawkey', 'tag'])
    print(blue('RawToTag: success. We have total {:,} rawToTags.'.format(len(rawToTag))))
    print(df_rawToTag)

    return df_rawToTag


def genTagSet(keylist=None, akaDict=None) :
    tagDict = genTagDict(keylist, akaDict)
    rawToTag = genRawToTag(tagDict)

    return tagDict, rawToTag
