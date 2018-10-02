# Copyright 2018 Cerebro Scholar
# generated by JE KIM
"""
modules for importing DB(papers, links) from AWS or local
1) from AWS,
papers, links = importDB_AWS()

3) from local,
papers, links = importDB_stored(filename)
"""

import pandas as pd
from printUtils import *

def importDB_AWS() :
    print(blue('Importing latest DB from AWS.'))

    from AWS_SDK import RDS
    RDS = RDS()

    papers = pd.read_sql("SELECT * from paper", RDS.conn)
    links = pd.read_sql("SELECT * from link", RDS.conn)

    print(blue("Success. Now we have '{:,} papers' and '{:,} links'.".format(len(papers), len(links))))
    print('- papers :', papers.columns.tolist())
    print('- links :', links.columns.tolist())

    return papers, links

def importDB_stored(filename = 'backupdb.db'):
    print(blue("Importing DB from '{}'".format(filename)))
    import sqlite3
    import os.path

    if not os.path.isfile(filename) :
        print(red("'{}' does not exist. Please check the filename.".format(filename)))
        return None,None

    # conn = sqlite3.connect('db2_13585_32480.db')
    conn = sqlite3.connect(filename)

    papers = pd.read_sql('select * from paper', conn)
    links = pd.read_sql('select * from links', conn)

    print(blue("Success. Now we have '{:,} papers' and '{:,} links'.".format(len(papers), len(links))))
    print('- papers :', papers.columns.tolist())
    print('- links :', links.columns.tolist())

    return papers, links


