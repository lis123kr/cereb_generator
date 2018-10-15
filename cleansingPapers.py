# Copyright 2018 Cerebro Scholar
# generated by JE KIM
"""
cleasning and extracting representative values of papers.

columns : 
    ['p_id', 'title', 'abstract', 'keywords_author', 'keywords_other', 
    'max_cite', 'pub_year', 'sources']
    
    publication, author - not include.

use :
    papers_cleanse = cleansing_papers(papers, [keywordCase: source list for keyword])
"""

import ast
import numpy as np
import pandas as pd
from printUtils import *
pd.options.mode.chained_assignment = None

def dt(string) :
    """json to dict"""
    if string == None : return {}
    return ast.literal_eval(string)

def cleanse_title(x) :
    titles = dt(x)
    if 'axv' in titles.keys() : title = titles['axv']
    elif 'scp' in titles.keys() : title = titles['scp']
    elif 'wos' in titles.keys() : title = titles['wos']
    elif 'ieee' in titles.keys() : title = titles['ieee']

    if title :
        return title
    else:
        return np.nan


def cleanse_ncite(x) :
    cites = list(filter(None.__ne__, list(dt(x).values())))
    cites = list(map(int, cites))

    if len(cites) > 0 :
        return max(cites)
    else:
        return np.nan

def cleanse_pubyear(x) :
    # arXiv의 경우 arXiv년도 선택 (bibtext parsing으로 얻은 년도의 신뢰성보다 아카이브자체의 년도 신뢰성이 높음)
    # 빈도수 높은 년도로 선택. ex) SCP=2017, IEEE=2018, ARX=2017, WOS=NAN ==> 2017
    yeardict = dt(x)
    if 'axv' in yeardict.keys() : years = [int(yeardict['axv'])]
    else : 
        years = list(filter(None.__ne__, list(yeardict.values())))
        years = list(map(int, years))

    if len(years) > 0 :
        return max(set(years), key=years.count)
    else:
        return np.nan

def cleanse_keywords(x, case=['scp', 'wos', 'ieee']) :
    json = dt(x['keywords'])
    keyindex_author = ['author_keywords', 'Author Keywords']

    keywords = {'author':[],'plus':[]}

    for source in case :
        try : 
            for k,v in dt(json[source]).items() :
                if k in keyindex_author :
                    keywords['author'].extend(v)
                else :
                    keywords['plus'].extend(v)
        except : 
            pass           


    if len(keywords['author'])==0 : keywords['author'] = np.nan
    else : 
        # set keys while maintaining order
        uni = set(keywords['author'])
        keywords['author'] = [x for x in keywords['author'] if x in uni]

    if len(keywords['plus'])==0 : keywords['plus'] = np.nan
    else : 
        # set keys while maintaining order
        uni = set(keywords['plus'])
        keywords['plus'] = [x for x in keywords['plus'] if x in uni]           
        # keywords['plus'] = list(set(keywords['plus']))

    return keywords


def cleansing_papers(papers, keywordCase=['scp', 'wos', 'ieee']) :
    print(blue('\n=> Cleansing and extracting representative values of papers..'))

    temp = papers.loc[:,['p_id', 'title', 'n_cite', 'pub_year', 'keywords' , 'abstract']]
    temp["sources"] = temp.title.apply(lambda x :str(list(dt(x).keys())))
    temp["title"] = temp.title.apply(cleanse_title)
    temp["max_cite"] = temp.n_cite.apply(cleanse_ncite)
    temp["pub_year"] = temp.pub_year.apply(cleanse_pubyear)
    keywords = temp.apply(lambda x: cleanse_keywords(x, case=keywordCase), axis=1)
    temp["keywords_author"] = keywords.apply(lambda x : x['author'])
    temp["keywords_other"] = keywords.apply(lambda x : x['plus'])

    # temp['abstract'] = temp.abstract.apply(lambda x :np.nan if (x==None) else x)
    # temp['title'] = temp.title.apply(lambda x :np.nan if (x==None) else x)

    temp.abstract[temp.abstract.isna()] = np.nan
    temp.title[temp.title.isna()] = np.nan

    dataset = temp[['p_id', 'title', 'abstract', 'keywords_author', 'keywords_other', 'max_cite', 'pub_year', 'sources']] 
    # dataset.columns = ['p_id', 'title', 'abstract', 'keywords_author', 'keywords_other', 'max_cite', 'pub_year', 'sources']

    pd.set_option('display.max_colwidth', 30)
    pd.set_option('display.max_rows', 10)

    print(blue('Done.'))
    print(dataset)

    return dataset
