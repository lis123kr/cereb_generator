# Copyright 2018 Cerebro Scholar
# generated by JE KIM
"""
Additional cleansing for assigned scholarly keywords.

use:
papers_clean,keylist = additional_cleansing_for_keywords
                        (papers_clean, 
                        [keytype : colum to deep clean.(default is 'keywords_author')])
"""
import pandas as pd
from printUtils import *

def AdditionalCleanse(keylist) :
    import re
    global AKA
    # temp = 'differential evolution (de), direct search, evolutionary algorithms (eas)'
    temp = ", ".join(keylist)    
    
    def checkinside(x) :
        m = re.compile(r'[(].*?[)]').finditer(temp)
        for i in m :
            if (i.span()[0] < x) and (x < i.span()[1]) :
                return True
        return False 

    comma_p = [i for i,c in enumerate(temp) if c==',' and not checkinside(i)]
    keys = []

    if(len(comma_p) == 0) :
        key = temp
    else :
        key = temp[:comma_p[0]].strip()
        
    if(len(key)>0) :
        if((key[0]=="'" and key[len(key)-1] == "'") or (key[0]=='"' and key[len(key)-1] == '"')) :
            key = key[1:len(key)-1]
        if(key[len(key)-1] == '.') : key = key[:len(key)-1]
            
        keys.append(key)
        
        
    for i,x in enumerate(comma_p) :
        if i == len(comma_p)-1 :
            key = temp[x+1:].strip()
        else :
            key = temp[comma_p[i]+1:comma_p[i+1]].strip()
            
        if(len(key)==0) : continue
        elif((key[0]=="'" and key[len(key)-1] == "'") or (key[0]=='"' and key[len(key)-1] == '"')) :
            key = key[1:len(key)-1]

        # elif (key[0]=="(" and key[len(key)-1] == ")") :
        #     print({'short' : key[1:len(key)-1], 'long' : keys[len(keys)-1]})
        #     if AKA is None : AKA = []
        #     AKA = AKA.append({'short' : key[1:len(key)-1], 'long' : keys[len(keys)-1]})
        #     continue
            
        if(key[len(key)-1] == '.') : key = key[:len(key)-1]
            
        keys.append(key)
    return list(set(keys))


def getkeys_withAdditionalCleanse(x, keytype, keylist) :
    # print(x[keytype])
    # jj = AdditionalCleanse(x[keytype])
    # if(len(set(jj)) != len(jj)) : print('problem solving!!')
    cleanseKeys = list(set(AdditionalCleanse(x[keytype])))
    # print(cleanseKeys)
    for key in cleanseKeys : 
        keylist.append({
            'key' : key.lower(),
            'p_id' : x.p_id,
            'year' : x.pub_year,
            'n_cite' : x.max_cite
        })
    return cleanseKeys

# AdditionalCleanse(dataset.keywords_author[papers.p_id==np.int64(10823)].values[0])
# AKA = []
# AdditionalCleanse(['Deep learning', 'Deep Convolutional Neural Networks, (DCNNs)', 'Universal features', 'Retinal image analysis', 'Age -related macular degeneration, (AMD)', 'Transfer learning'])


def Detail_check(df, p_id=52738) :
    df.set_index('p_id', inplace=True)
    
    a = df.loc[p_id, 'keywords_author']
    print('before :', a)
    b = df.loc[p_id, 'keywords_author_moreclean']
    print('after :', b)

    if set(a)==set(b) : print('===> SAME')
    else : print('===> NOT SAME')

    return
        
def what_different(df, ex_num=5) :
    pd.set_option('display.max_colwidth', 100)

    df_notna = df[df.keywords_author.isna() == False]
    a = df_notna.keywords_author.apply(set)
    b = df_notna.keywords_author_moreclean.apply(set)

    print(blue('{:,} papers\' keywords have been cleansed additionally.\n'.format(sum(a!=b))))
    print('\nCheck Details...')
    print('* source variation follows')
    print(df_notna[a!=b].sources.value_counts())
    
#     print('='*10)
#     display(df_notna[a!=b].head(3))
#     display(df_notna[a!=b].loc[:,['keywords_author', 'keywords_author_moreclean']])

    print()
    print('* Check carefully the changes. Here\'s 5 examples.')
    print()
    exs = df_notna[a!=b][:ex_num].loc[:, 'p_id'].values
    for ex in exs:
        print('p_id :', ex)
        Detail_check(df.copy(), p_id=ex)
        print()
    
    return

def lower(keylist) :
    # print(keylist)
    if len(keylist) < 1 : return []
    return [each.lower() for each in keylist]

def additional_cleansing_for_keywords(papers_clean, keytype = 'keywords_author') :
    print(blue('Additional cleansing for {}...'.format(keytype)))

    keylist = []
    newcol = keytype + '_moreclean'
    papers_clean[newcol] = papers_clean[papers_clean[keytype].isna() == False].apply(lambda x : getkeys_withAdditionalCleanse(x, keytype, keylist), axis=1)

    if 'rawkeys' in papers_clean.columns :
        papers_clean['rawkeys'] = papers_clean[(papers_clean[newcol].isna() == False) & (papers_clean.rawkeys.isna() == False)].apply(lambda x: list(set(x.rawkeys + lower(x[newcol]))), axis=1)
        papers_clean['rawkeys'] = papers_clean[(papers_clean[newcol].isna() == False) & (papers_clean.rawkeys.isna() == True)].apply(lambda x: list(set(lower(x[newcol]))), axis=1)
    else :
        papers_clean['rawkeys'] = papers_clean[papers_clean[newcol].isna() == False].apply(lambda x: lower(x[newcol]), axis=1)

    what_different(papers_clean)
    return papers_clean, keylist