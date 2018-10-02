# Copyright 2018 Cerebro Scholar
# generated by JE KIM
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

def step1_stem_compare(df_rawkeys) :
    print(yellow('Step1. Stem and compare.'))
    
    unique = df_rawkeys.key.value_counts()

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

    print(yellow('Done. {:,} unique rawkeys are clustered to {:,} tags').format(len(uni_keys), len(tagDict)))

    return tagDict

def combine_tags() :

    return


def genTagDict(keylist=None) :
    print(blue('Generating tagDict...'))
    if keylist is None :
        print('TODO : get keylist from cerebDB directly')
        return
    
    df_rawkeys = pd.DataFrame(keylist, columns=['key', 'p_id', 'year', 'n_cite']).sort_values(by=['key'])
    df_rawkeys.drop_duplicates(['p_id','key'], inplace=True)

    tagDict = step1_stem_compare(df_rawkeys)



    tagDict.set_index('tag', inplace=True)

    print(blue('TagDict: Success. From {:,} rawkeys, unique {:,} tags are generated.'.format(len(df_rawkeys), len(tagDict))))
    # print(df_rawkeys.key.value_counts())
    print(tagDict)

    return tagDict

def spreading(x, rawToTag) :
    for each in x.rawkeys :
        rawToTag.append({'rawkey' : each, 'tag' : x.tag })

def genRawToTag(tagDict) :
    print(blue('Generating RawToTag...'))

    dictTemp = tagDict.reset_index()
    rawToTag = []

    dictTemp.apply(lambda x:spreading(x, rawToTag), axis=1)
    df_rawToTag = pd.DataFrame(rawToTag, columns=['rawkey', 'tag'])
    print(blue('RawToTag: success. We have total {:,} rawToTags.'.format(len(rawToTag))))
    print(df_rawToTag)

    return df_rawToTag


def genTagSet(keylist=None) :
    tagDict = genTagDict(keylist)
    rawToTag = genRawToTag(tagDict)

    return tagDict, rawToTag
