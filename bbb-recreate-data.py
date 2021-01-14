# Re-create the BBB data (individual assignment)
#
# A dataset like BBB doesn't exist in companies in its raw form
# Someone has to create it first ... likely from different data sources!
#
# The goal of this assignment is to re-create the pandas data frame in bbb.pkl
# data EXACTLY from its components. Follow the steps outlined below:
#
# 1. Determine how to load the different file types (use pd.read_pickel, pd.read_csv,
#    pd.read_excel, and sqlite3.connect)
# 2. Determine what data transformations are needed and how the data should be
#    combined into a data frame. You MUST name your re-created data frame 'bbb_rec'
# 3. Your work should be completely reproducible (i.e., generate the same results on
#    another computer). Think about the 'paths' you are using to load the data. Will
#    I or the TA have access to those same directories? Of course you cannot 'copy'
#    any data from bbb into bbb_rec. You can copy the data description however
# 4. The final step will be to check that your code produces a data frame
#    identical to the pandas data frame in the bbb.pkl file, using pandas' "equals"
#    method shown below. If the test passes, write bbb_rec to "data/bbb_rec.pkl". Do
#    NOT change the test as this will be used in grading/evaluation
# 5. Make sure to style your python code appropriately for easy readable
# 6. When you are done, save your, code and commit and push your work to GitLab.
#    Of course you can commit and push as often as you like, but only before the
#    due date. Late assignments will not be accepted
# 7. When testing your (final) code make sure to restart the kernel regularly.
#    Restarting the kernel ensures that all modules and variables your code needs
#    are actually generated and loaded in your code
# 8. You can use modules other than the ones mentioned below but do NOT use
#    modules that are not part of the rsm-msba-spark docker container by default

import pandas as pd
import sqlite3
from datetime import date
import pyrsm as rsm
import urllib.request
from tempfile import NamedTemporaryFile as tmpfile
import os
import numpy as np

# load the original bbb.pkl data frame from a Dropbox link
bbb_file = tmpfile().name
urllib.request.urlretrieve(
    "https://www.dropbox.com/s/6bulog0ij4pr52o/bbb.pkl?dl=1", bbb_file
)
bbb = pd.read_pickle(bbb_file)

# view the data description of the original data to determine
# what needs to be re-created
rsm.describe(bbb)

# set the working directory to the location of this script
os.getcwd()
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

# load demographics data from bbb_demographics.tsv
bbb_demographics=pd.read_csv('data/bbb_demographics.tsv', sep='\t')
bbb_demographics['zip'] = bbb_demographics['zip'].apply(lambda x : '{:0>5d}'.format(x))

# load nonbook aggregate spending from bbb_nonbook.xls
bbb_nonbook=pd.read_excel('data/bbb_nonbook.xls')
# load purchase and buy-no-buy information from bbb.sqlite
# mydb=sqlite3.connect("rsm-mgta455-bbb-recreate-data/data/bbb.sqlite")
# cursor=mydb.cursor()
# cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# Tables=cursor.fetchall()
# print(Tables)
# cursor.execute("PRAGMA table_info(buyer)")
# print(cursor.fetchall())

con =  sqlite3.connect('data/bbb.sqlite') 
buyer = pd.read_sql_query("SELECT * FROM buyer", con=con)
purchase = pd.read_sql_query("SELECT * FROM purchase", con=con)
con.close()
purchase['date']=pd.to_datetime(purchase['date'],origin='unix',unit='D')
# hint: what data type is "date" in the database?
# hint: most systems record dates internally as the number
# of days since some origin. You can use the pd.to_datetime
# method to convert the number to a date with argument: origin = "1-1-1970"
# db_list_tables(con)
# buyer = db_list_fields(con,'buyer')

def db_list_tables(con):
    """Return all table names"""
    cursor = con.cursor()
    cursor.execute("select name from sqlite_master where type='table';")
    return [x[0] for x in cursor.fetchall()]


def db_list_fields(con, tabel):
    """Return all column names for  specified table"""
    cursor = con.cursor()
    print(cursor.description)
    cursor.execute(f"select * from {tabel} limit 1;")
    return [name[0] for name in cursor.description]

  
# add the zip3 variable
bbb_demographics['zip3']=bbb_demographics['zip'].str[:3]
# use the following reference date (i.e., "today" for the analysis)
start_date = date(2010, 3, 8)
start_date = pd.Timestamp(start_date)

def diff_months(date1, date2):
    """
    This function calculates the difference in months between
    date1 and date2 when a customer purchased a product
    """
    y = date1.year - date2.year
    m = date1.month - date2.month
    return y * 12 + m




# generate the required code below for `first`, `last`, `book`, and `purch`,


first = purchase.groupby(['acctnum'])['date'].min().reset_index()
first['start']=start_date

first['first']=first.apply(lambda row: diff_months(row['start'], row['date']), axis=1)

last = purchase.groupby(['acctnum'])['date'].max().reset_index()
last['start']=start_date
last['last']=last.apply(lambda row: diff_months(row['start'], row['date']), axis=1)

book = purchase.groupby(['acctnum'])['price'].sum().reset_index()
purch = purchase.groupby(['acctnum'])['purchase'].count().reset_index()

type_book= purchase.groupby(['acctnum'])['purchase'].value_counts().unstack().fillna(0)

# and add the purchase frequencies for the different book types
# hint: you can use pandas "value_counts" method here
# hint: check the help for pandas' `first` and `last` methods

# you may find the discussion below of interest at this point
# https://stackoverflow.com/questions/65067042/pandas-frequency-of-a-specific-value-per-group
bbb_rec = bbb_demographics.merge(bbb_nonbook,on = 'acctnum')
first = first[['acctnum','first']]
last = last[['acctnum','last']]
bbb_rec['acctnum']=bbb_rec['acctnum'].astype('str')
bbb_rec = bbb_rec.merge(first,on = 'acctnum').merge(last,on = 'acctnum').merge(book,on = 'acctnum').merge(purch,on = 'acctnum').merge(buyer, on = 'acctnum').merge(type_book,on = 'acctnum')

bbb_rec['book']=bbb_rec['price']
bbb_rec['total']=bbb_rec['book']+bbb_rec['nonbook']
bbb_rec['purch']=bbb_rec['purchase']
bbb_rec = bbb_rec[['acctnum','gender','state','zip','zip3','first','last','book','nonbook',	'total','purch','child','youth','cook','do_it','reference','art','geog','buyer','training']]

# combine the different data frames using pandas' "merge" method

# check if the columns in bbb and bbb_rec are in the same order
# and are of the same type - fix as needed
#category transform
cat_part = bbb_rec[['gender','state','buyer']].astype('category')
int32_part = bbb_rec[['first','last','book','nonbook','total','purch','child','youth','cook','do_it','reference','art','geog','training']].astype(np.int32)
obj_part = bbb_rec[['acctnum','zip','zip3']].astype('str')
bbb_rec = pd.concat([cat_part,int32_part,obj_part], axis=1)
bbb_rec = bbb_rec[['acctnum','gender','state','zip','zip3','first','last','book','nonbook',	'total','purch','child','youth','cook','do_it','reference','art','geog','buyer','training']]

#object

pd.DataFrame(
    {
        "bbb_rec": bbb_rec.dtypes.astype(str),
        "bbb": bbb.dtypes.astype(str),
        "check": bbb_rec.dtypes == bbb.dtypes,
    }
)

# add the description as metadata to bbb_rec (see data/bbb_description.txt)
# see https://stackoverflow.com/a/40514650/1974918 for more information

txt_url = "data/bbb_description.txt"
text=list()
with open(txt_url, "r") as f:  # 打开文件
    data = f.read()  # 读取文件
    text.append(data)
text=str(text)
text = text.replace('"]','')
text = text.replace('["','')
text = eval(repr(text).replace('\\\\', '\\'))
bbb_rec.description = text
bbb_rec._metadata.append('description')
bbb_rec.description
# check that you get the same output for both bbb and bbb_rec
rsm.describe(bbb_rec)
rsm.describe(bbb)

#############################################
# DO NOT EDIT CODE BELOW THIS LINE
# YOUR CODE MUST PASS THE TEST BELOW
#############################################
test1 = bbb_rec.equals(bbb)
if hasattr(bbb_rec, "description"):
    test2 = bbb_rec.description == bbb.description
else:
    test2 = False

print(test1)
print(test2)
if test1 is True and test2 is True:
    print("Well done! Both tests passed!")
    print("bbb_rec will now be written to the data directory")
    bbb_rec.to_pickle("data/bbb_rec.pkl")
else:
    test = False
    if test1 is False:
        raise Exception(
            """Test of equality of data frames failed.
            Use bbb.dtypes and bbb_rec.dtypes to check
            for differences in types. Check the number
            of mistakes per colmun using, for example,
            (bbb_rec["book"] == bbb["book"]).sum()"""
        )
    if test2 is False:
        raise Exception(
            """Add a description to the bbb_rec data frame.
            Read the description from the txt file in the
            data directory. See
            https://stackoverflow.com/a/40514650/1974918
            for more information"""
        )
