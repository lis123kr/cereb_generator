# Copyright 2018 Cerebro Scholar
# generated by IL SEOP Lee
"""
cleasning authors. 
	fullname
		1. latin character to english
		2. whitespace consistency after '.'
		3. remove '.' exception & 'and', 'et al' and so on..
	name_chk_key
		4. delete all special character except for '.'

columns : 
	['p_id_is_cited', 'by_p_id']

use :
	authors_clean = cleansing_authors(papers_clean)
"""
import re, ast, time
from printUtils import red, blue, yellow
from authors import Author
import pandas as pd
import numpy as np
import warnings	
warnings.filterwarnings("ignore")

def generate_cerebauthor_dict(paper_):
	fullauthors, normalname, hardname = make_fullauthors( paper_.to_dict(orient="records") )
	df = pd.DataFrame.from_dict(fullauthors, orient='index')

	df = share_info_among_same_people(df)

	# use name_chk_key for fullauthors
	notdup, dupdup = split_dup_or_notdup(df, also_namekey=True)

	# Assign cereb_auid to fullauthors
	cbid = [0]
	notdup['cereb_auid'] = notdup.apply(lambda x : assign_cerebauid(cbid), axis=1)
	print(blue("assigned cereb_auid to full-authors, len : {}".format(len(notdup))))

	# not process others & dup-with-fullauthor 
	
	normal_df = pd.DataFrame(normalname)[['fullname', 'lastname', 'name_chk_key', 'firstname', 'keywords', 'email', 'affiliations', 'publications', 'wos_auid', 'scp_auid', 'name_variants']]
	hard_df = pd.DataFrame(hardname)[['fullname', 'lastname', 'name_chk_key', 'firstname', 'keywords', 'email', 'affiliations', 'publications', 'wos_auid', 'scp_auid', 'name_variants']]
	others = pd.DataFrame().append(normal_df,sort=False).append(hard_df,sort=False)
	others = others.append(dupdup,sort=False).reset_index(drop=True) 

	others = share_info_among_same_people(others, iselse=True)

	print(blue("recogizing fullauthor in list of others"))
	d1,d2,d3,d4 = get_isin_dict(notdup, ['scp_auid', 'wos_auid', 'email', 'name_chk_key'])

	others['cereb_auid'] = others[['scp_auid', 'email', 'wos_auid', 'name_chk_key']].apply(lambda x : assign_cerebauid_dup_check(x, d1, d2, d3, d4), axis=1)
	
	dup_with_fullauthor = others[ others['cereb_auid'].isnull()==False ]
	others_else = others[ others['cereb_auid'].isnull() ]

	dfupdated = notdup.append(dup_with_fullauthor.set_index('name_chk_key', drop=False), sort=False)
	print(blue("DONE recogizing fullauthor in list of others"))

	print(blue("\nprocessing others"))
	# not use name_chk_key for others... we cannot sure they are identical person.
	others_notdup, others_dupdup = split_dup_or_notdup(others_else, also_namekey=False)

	# Assign cereb_auid to unique pepple of others 
	others_notdup['cereb_auid'] = others_notdup.apply(lambda x : assign_cerebauid(cbid), axis=1)
	
	d1,d2,d3,d4 = get_isin_dict(others_notdup, ['scp_auid', 'wos_auid', 'email', 'name_chk_key'])
	others_dupdup['cereb_auid'] = others_dupdup[['scp_auid', 'email', 'wos_auid', 'name_chk_key']].apply(lambda x : assign_cerebauid_dup_check(x, d1, d2, d3, d4), axis=1)
	print(" checking not assigend length {}".format(len(others_dupdup[ others_dupdup['cereb_auid'].isna() ])))

	total_df = dfupdated.append(others_notdup.set_index('name_chk_key', drop=False), sort=False)
	total_df = total_df.append(others_dupdup.set_index('name_chk_key', drop=False), sort=False)

	print(blue("processing others done... now making cereb_authors_dict"))
	# total_df.to_pickle("total_df.pkl")
	def to_None(x):
		if x==None or len(x) == 0:
			return None
		elif type(x)==dict and len(list(x.keys()))==0:
			return None
		else:
			return x
	total_df['affiliations'] = total_df['affiliations'].apply(lambda x : to_None(x))
	total_df['keywords'] = total_df['keywords'].apply(lambda x : to_None(x))

	namekey_to_cerebid = total_df[['name_chk_key', 'cereb_auid']].groupby(by='name_chk_key').agg({
		'cereb_auid' : lambda x : list(set(x))
	})
	namekey_to_cerebid['cereb_auid'] = namekey_to_cerebid['cereb_auid'].apply(lambda x : x[0] if len(x) == 1 else x)

	cerebgroup = total_df.groupby(by='cereb_auid').agg({
		'fullname' : lambda x : x.iloc[0],
		'lastname' : lambda x : get_(x),
		'name_chk_key' : lambda x: x.iloc[0],
		'firstname' : lambda x : get_(x),
		'keywords' : lambda x : merge_keywords(x),
		'email' : lambda x : get_(x),
		'affiliations' : lambda x : x.iloc[0],
		'publications' : lambda x : x.iloc[0],
		'wos_auid' : lambda x : get_(x),
		'scp_auid' : lambda x : get_(x),
		'name_variants' : sum
	})
	# cerebgroup.to_pickle("cerebgroup.pkl")
	
	cerebauthor_dict = dict()
	cerebgroup['cereb_auid'] = cerebgroup.index
	for c in ['scp_auid', 'wos_auid', 'email']:
		cerebauthor_dict[c] = cerebgroup[ cerebgroup[c].isnull() == False][[c, 'cereb_auid']].set_index(c).to_dict(orient='index')
	cerebauthor_dict['name_chk_key'] = namekey_to_cerebid.to_dict(orient='index')
	for name in cerebauthor_dict['name_chk_key'].keys():
		if type(cerebauthor_dict['name_chk_key'][name]['cereb_auid']) == list:
			cerebauthor_dict['name_chk_key'][name]['cereb_auid'] = [ id_ for id_ in cerebauthor_dict['name_chk_key'][name]['cereb_auid'] if id_ != None]
	return cerebauthor_dict, cerebgroup

def share_info_among_same_people(df, iselse=False):
	def sharing(x, dict_, k1, k2):
		if x[k1] != None:
			return dict_[x[k1]][k2]
		return x[k2]

	start_time = time.time()	
	scpagg = df.groupby(by='scp_auid').agg({
		'email' : lambda x : get_(x),
		'wos_auid' : lambda x : get_(x)
	})
	wosagg = df.groupby(by='wos_auid').agg({
		'email' : lambda x : get_(x),
		'scp_auid' : lambda x : get_(x)
	})
	emailagg = df.groupby(by='email').agg({
		'scp_auid' : lambda x : get_(x),
		'wos_auid' : lambda x : get_(x)
	})
	if iselse: print(yellow("=> others & dup-with-fullauthor "))
	else: print(yellow("=> Full-authors"))
	print(yellow("num of author : {}, scp_auid : {}, wos_auid : {}, email : {} ".format(len(df),len(scpagg), len(wosagg), len(emailagg))))
	print(yellow("share ids among the people who have id, email..."))

	scpaggdict = scpagg.to_dict(orient='index')
	wosaggdict = wosagg.to_dict(orient='index')
	emailaggdict = emailagg.to_dict(orient='index')

	df['wos_auid'] = df[['scp_auid', 'wos_auid']].apply(lambda x : sharing(x,scpaggdict, 'scp_auid', 'wos_auid'), axis=1)
	df['email'] = df[['scp_auid', 'email']].apply(lambda x : sharing(x,scpaggdict, 'scp_auid', 'email'), axis=1)

	df['scp_auid'] = df[['wos_auid', 'scp_auid']].apply(lambda x : sharing(x,wosaggdict, 'wos_auid', 'scp_auid'), axis=1)
	df['email'] = df[['wos_auid', 'email']].apply(lambda x : sharing(x,wosaggdict, 'wos_auid', 'email'), axis=1)

	df['scp_auid'] = df[['email', 'scp_auid']].apply(lambda x : sharing(x,emailaggdict, 'email', 'scp_auid'), axis=1)
	df['wos_auid'] = df[['email', 'wos_auid']].apply(lambda x : sharing(x,emailaggdict, 'email', 'wos_auid'), axis=1)

	e = int(time.time() - start_time)
	DuringTime(start_time, "share_info_among_same_people DONE!")
	return df

def split_dup_or_notdup(df, also_namekey=False):
	cond1 = np.logical_and((df[['scp_auid']].isnull() == False), df[['scp_auid']].duplicated().to_frame())
	cond2 = np.logical_and((df[['wos_auid']].isnull() == False), df[['wos_auid']].duplicated().to_frame())
	cond3 = np.logical_and((df[['email']].isnull() == False), df[['email']].duplicated().to_frame())
	cond4 = False

	if not also_namekey:
		cond4 = np.logical_and((df[['name_chk_key']].isnull() == False), df[['name_chk_key']].duplicated().to_frame())

	cond = np.logical_or( np.logical_or(cond1, cond2), np.logical_or(cond3, cond4) )

	notdup, dupdup = df[ np.logical_not( cond ).values ],  df[ (cond).values]
	print(yellow("Duplicated data : {}, else : {}".format(len(dupdup), len(notdup))))
	return notdup, dupdup

def make_fullauthors(paperdict):
	fullauthors, normalname, hardname = dict(), [], []
	starttime = time.time()
	for p in paperdict:
		if str(p['authors']) == 'nan': continue
		axvauthor, scpauthor, wosauthor, ieeeauthor = get_authors_list(p['authors'])
		publications = p['publication']
		keywords = p['tags']

		for a, s, w, i in zip(axvauthor, scpauthor, wosauthor, ieeeauthor):
			full, variations, src_ = get_fullnames(a,s,w,i)
			match = re.compile(r'( and )').search(full)
			if match:
				full_ = re.compile(r'( and )').sub("&", full)
				fullsplit = full_.split('&')
				if len(fullsplit) == 2 and (len(fullsplit[0].strip()) <= 3 or len(fullsplit[0].split(' ')) == 1):
					# author 한명으로
					full = full_.replace('&', ' ').strip()
				else:
					# 2명 이상
					for idf, f in enumerate(fullsplit):
						if f.strip() == '': continue
							
						f = cleansing_fullname(f.strip())[1]
						if f.strip() == '' or f.strip() == '.': continue
							
						au = Author(publications, keywords, f, src_)
						newv = [denoising_name(f)]
						au.update_au(a,s,w,i)
						au.name_variants = newv
						
						classification_author(au, fullauthors, normalname, hardname)					
					continue
			if full.strip() != '' and full.strip() != '.':
				au = Author(publications, keywords, full, src_)
				au.update_au( a,s,w,i )
				au.name_variants = list(set(variations))
				
				classification_author(au, fullauthors, normalname, hardname)

	DuringTime(starttime, "make_fullauthors Done!!")
	print(blue("fullauthors : {}, Normal : {}, Hard : {}".format(len(fullauthors.keys()), len(normalname), len(hardname))))
	return fullauthors, normalname, hardname

def get_isin_dict(df, cols):
	dkey = []
	for c in cols:
		dkey.append(df[ df[c].isnull() == False ][[c, 'cereb_auid']].set_index(c).to_dict(orient='index'))
	return dkey	

def denoising_name(x):
	from unidecode import unidecode
	x = unidecode(x)
	x = x.replace('.', '. ').strip()

	# continuous whitespace to one whitespace
	if re.compile(r'\s\s+').search(x):
		x = re.compile(r'\s\s+').sub(' ', x).strip()

	# remove whitespace before '.'
	if re.compile(r'\s+\.').search(x):
		x = re.compile(r'\s+\.').sub('.', x)

	if x[-1] == '.':
		x = x[:-1].strip()
	if x != '' and x[0] == '.':
		x = x[1:].strip()
	if x != '' and x[:4] == 'and ':
		x = x[4:].strip()
	if x != '' and x[-4:] == ' and':
		x = x[:-4].strip()
		
	if re.compile(r' ?et al\.?').search(x):
		x = re.compile(r' ?et al\.?').sub('',x).strip()
	return x

def cleansing_fullname(x, denoising=False):
	ori = x.strip()
	if x == '': return x
	if denoising:
		x = denoising_name(x)
	# remove all special character except for '.' and whitespace
	# delete '-' -> better?
	if re.compile(r'([^\w\.\s]|[0-9])').search(x):
		x = re.compile(r'([^\w\.\s]|[0-9])').sub("", x)

	namekey = x.replace(' ', '').lower()
	return ori, x , namekey

def get_authors_list(aus):
	authors = ast.literal_eval(str(aus))
	axvauthor = ast.literal_eval(str(authors.get('axv', '[]')))
	scpauthor = ast.literal_eval(str(authors.get('scp', '[]')))
	wosauthor = ast.literal_eval(str(authors.get('wos', '[]')))
	ieeeauthor = ast.literal_eval(str(authors.get('ieee', '[]')))
	if wosauthor == None:
		wosauthor = []
	if ieeeauthor == None:
		ieeeauthor = []
	if scpauthor == None:
		scpauthor = []
	if axvauthor == None:
		axvauthor = []

	maxleng = max(len(axvauthor), len(scpauthor), len(wosauthor), len(ieeeauthor))
	while len(axvauthor) != maxleng:
		axvauthor.append(None)

	while len(scpauthor) != maxleng:
		scpauthor.append(None)

	while len(wosauthor) != maxleng:
		wosauthor.append(None)

	while len(ieeeauthor) != maxleng:
		ieeeauthor.append(None)

	return axvauthor, scpauthor, wosauthor, ieeeauthor

def get_fullnames(a,s,w,i):
	full, src_ = '', ''
	variations = []

	if a and a.get('fullname'):
		full = a['fullname']
		src_= 'axv'
		variations.append(full)
	if s and s.get('firstname') and s.get('lastname'):
		if full == '':
			src_ = 'scp'
			full = s.get('firstname')+" "+s.get('lastname')
		variations.append(s.get('firstname')+" "+s.get('lastname'))

	if i and i.get('fullname'):
		if full == '':
			src_ = 'ieee'
			full = i['fullname']
		variations.append(i['fullname'])
	
	if w and w.get('firstname', '') != '' and w.get('lastname', '') != '':
		if full == '':
			src_ = 'wos'
			full = w.get('firstname')+" "+w.get('lastname')
		variations.append(w.get('firstname')+" "+w.get('lastname'))
	if s and s.get('fullname'):
		if full == '':
			src_ = 'scp'
			full = s.get('fullname')
		variations.append(s.get('fullname'))
	if w and w.get('fullname'):
		if full == '':
			src_ = 'wos'
			full = w.get('fullname')
		variations.append(w.get('fullname'))
	if full != '':
		_, full, _ = cleansing_fullname(full, denoising=True) #make_name_chk_key(full)
		
	if len(variations):
		for i in range(len(variations)):
			variations[i] = denoising_name(variations[i])

	return full, list(set(variations)), src_

def is_firstname_abbreviated(x):
	if type(x) != str:
		print("is_f_a, x is not str, ",x)
		return False
	x = x.strip()
	match = re.compile(r'([A-Za-z]\.)').search(x[:2])
	if not match:
		return False
	return True

def recog_authors(au):
	if au.numofmiddlename >= 2 or (not is_firstname_abbreviated(au.fullname) and au.numofmiddlename >= 1):
		return 'easy'
	elif (is_firstname_abbreviated(au.fullname) and au.numofmiddlename >= 1) or not is_firstname_abbreviated(au.fullname):
		return 'normal'
	else:
		return 'hard'
					
def classification_author(au, fullauthors, normalname, hardname):
	def insert_or_update(au, authors):
		if au.name_chk_key:
			if authors.get(au.name_chk_key):
				# update keywords weight
				for k in au.keywords:
					if authors[au.name_chk_key]['keywords'].get(k):
						authors[au.name_chk_key]['keywords'][k] += 1
					else:
						authors[au.name_chk_key]['keywords'][k] = 1
				if not authors[au.name_chk_key]['email']:
					authors[au.name_chk_key]['email'] = au.email
				if not authors[au.name_chk_key]['affiliations']:
					authors[au.name_chk_key]['affiliations'] = au.affiliations
				if not authors[au.name_chk_key]['publications']:
					authors[au.name_chk_key]['publications'] = au.publications
				if len(authors[au.name_chk_key]['name_variants']):
					au.name_variants.extend(authors[au.name_chk_key]['name_variants'])
					authors[au.name_chk_key]['name_variants'] = list(set(au.name_variants))
			else:
				authors[au.name_chk_key] = au.to_dict()
		return
	r = recog_authors(au)
	if r == 'easy':
		insert_or_update(au, fullauthors)
	elif r=='normal':
		normalname.append( au.to_dict() )
	else:
		hardname.append( au.to_dict() )	
	return

def DuringTime(starttime, msg):
	e = int(time.time() - starttime)
	print('[TIME]{:02d}:{:02d}:{:02d},  {}'.format(e // 3600, (e % 3600 // 60), e % 60, msg))

def assign_cerebauid(cbid):
	cbid[0] = cbid[0]+1
	return 'cereb_'+str(cbid[0])

def assign_cerebauid_dup_check(x, d1,d2,d3,d4):
	if x['scp_auid'] != None and d1.get(x['scp_auid']):
		return d1[x['scp_auid']]['cereb_auid']
	if x['wos_auid'] != None and d2.get(x['wos_auid']):
		return d2[x['wos_auid']]['cereb_auid']
	if x['email'] != None and d3.get(x['email']):
		return d3[x['email']]['cereb_auid']
	if d4.get(x['name_chk_key']):
		return d4[x['name_chk_key']]['cereb_auid']
	return None

def get_(x):
	for i in x:
		if i!= None:
			return i
	return None

def merge_keywords(x):
	c = dict()
	for xx in x:
		if xx == None:
			continue
		if type(xx) != dict:
			continue
		for xk in xx.keys():
			c.setdefault(xk, 0)
			c[xk]+=1
	if len(list(c.keys()))==0:
		return None
	return c