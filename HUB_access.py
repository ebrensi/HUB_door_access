# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:48:54 2015

@author: Efrem
"""
   
import pandas as pd
import re

# This script reads a txt file containing an Integra Link events report      
def parse_text_report(text_file):
    p_date = re.compile('^\s*(\d+/\d+/\d+)') # this is the format for dates
    e_date = re.compile('(\d+)/(\d+)/(\d+)') # this is for extracting the date
    
    p_user = re.compile('^\s*(\d+:\d+ [AP]M) .* (ENTRY|EXIT) READER .* User: (\d+) (.*) ')
    e_time = re.compile('(\d+):(\d+) ([AP]M)')
    action2loc = {'ENTRY': 'OUTSIDE', 'EXIT': 'INSIDE'}
    
    fields = ['tstamp','Loc','UID','Name']

    date = []
    year = []
    tstamp = []
    time = []
    loc = []
    uid = []
    name = []
    yyyymmdd = '' 
    ## We're gonna loop through the lines of this text file
        #  Every line we care about is either a date or a user access record       
    print('Reading "%s"...') % text_file
    with open(text_file,'r') as f:
        for line in f:                
            date_match = p_date.match(line)
            if date_match:  # If this is a date line,
                            # set date to the date given on this line
                date_in = date_match.group(1)
                date_extract = e_date.match(date_in)
                
                # here we format the date as yyyy/mm/dd and pad wih zeros
                #  as necessary
                month, day, yr = date_extract.groups()
                yyyymmdd = '-'.join([yr, month.zfill(2), day.zfill(2)])                                
            else:
                user_match = p_user.match(line)
                # if this is a user access record, append the info
                if user_match:
                    time12, loc_in, uid_in, name_in = user_match.groups()
                    # convert time format from h:mm (AM|PM) to HH:MM 24-hr time
                    h,m,ap = e_time.match(time12).groups()
                    hour = int(h)
                    if ap == 'PM':
                        if hour < 12:
                            hour += 12
                    else: # then ap = 'AM'
                        if hour == 12:
                            hour = 0                  

                    time24 = ':'.join([str(hour).zfill(2), m.zfill(2)])
                           
                    year.append(yr)
                    date.append(month.zfill(2) + '-' + day.zfill(2))
                    time.append(time12)
                    tstamp.append(yyyymmdd + ' ' + time24)
                    loc.append(action2loc[loc_in])
                    uid.append(uid_in)
                    name.append(name_in)  
    
    df = pd.DataFrame(zip(year,date,time,tstamp,uid,name,loc),
                        columns=['Year','Date','Time','tstamp','UID','Name','Loc'])
    df['tstamp'] = pd.to_datetime(df.tstamp) #.set_index('tstamp')
    return df


def make_durations(df):    
    df = df.sort(['UID','tstamp'])
    df = df.reset_index(drop=True)
    loc_ind = df['Loc'].map( {'OUTSIDE':0, 'INSIDE':1} ).astype(int)
    check = loc_ind.diff()  # check == 1 where Loc is OUTSIDE followed by INSIDE 

    # We must disregard mistaken positives coming from 
    #   OUTSIDE from one person followed by INSIDE from another person
    firsts = df.groupby('UID').head(1).index  # First row of every UID group (Name) 
    check[firsts] = 0

    df['time_delta'] = df['tstamp'].diff()
    df['Period'] = df['time_delta'][check==1]/pd.np.timedelta64(1,'h')
    
    # Disregard any period of over 18 hours, which is silly
    df.loc[df['Period'] > 18, 'Period'] = None    
    df = df.drop('time_delta',axis=1)
 
    return df

def pivot_by_user(df):
    # We rearrange data into time series columns for each user
    #  we use 'last' as aggfunc.  This is hardly necessary but occasionally two events register
    #  on the same timestamp, in which case we just take the last one
    ts = pd.pivot_table(df, index=['tstamp'],columns=['UID','Name'],values='Loc',aggfunc='last')
    return ts 


def import_csv(fname):
    df = pd.read_csv(fname, names=['tstamp','Loc','UID','Name'], skiprows=[0])
    df.tstamp = pd.to_datetime(df.tstamp)
    df.Loc = df.Loc.astype('category')
    df.UID = df.UID.astype(int)
    return df

def group_by_user(df1,fname=False):
    df2 = make_durations(df1).sort('tstamp')
    
    df2 = factor_datetime_index(df2)    
    df_user = df2.sort(['UID','tstamp']).set_index(['UID','Name','Year','Date','Day','Time'])[['tstamp','Loc','Period']]
    df_user['tstamp'] = df_user.tstamp.map(lambda x:x.strftime('%Y/%m/%d %H:%M') )
    if fname:
        df_user.to_excel(fname, float_format = '%2.3f')
    return df_user
    


# ************** Main Code ********************
#r2 = parse_text_report('HUB_Door_Report_2_2015.txt',+1)['2/2015']
#r3 = parse_text_report('HUB_Door_Report_3_2015.txt')['3/2015']
#r4 = parse_text_report('HUB_Door_Report_4_2015.txt')['4/2015']
#r5 = parse_text_report('HUB_Door_Report_5_2015.txt')['5/2015']
#r6 = parse_text_report('HUB_Door_Report_6_2015.txt')['6/2015']

# r_all = pd.concat([r2,r3,r4,r5,r6]).sort_index()
# r_all.to_csv('HUB_Door_all.csv')


"""
df = pd.read_csv('HUB_Door_all.csv', names=['tstamp','Loc','UID','Name'], skiprows=[0])
df.tstamp = pd.to_datetime(df.tstamp)
df.Loc = df.Loc.astype('category')
df.UID = df.UID.astype(int)

UIDs = df[['UID','Name']].drop_duplicates().set_index('UID')
def UID(name):
    return UIDs[UIDs.Name.str.contains(name,case=False)]

print('%d unique user IDs') % df['UID'].nunique()
"""

"""
# Next we resample time series to one day intervals and indicate whether a user swiped a card that day
ts_days = ts.resample('D', how='count').astype(bool)
ts_days.sum(axis=1).plot(figsize=(15,5),title='total accesses by day')

dpw = ts_days.resample('W-Mon', how='sum')

def explore_user(uid):
    if uid == 'all':
        ts = df[['tstamp','Loc']]
    else:
        if not isinstance(uid, list):
            uid = [uid]
        ts = df[['tstamp','Loc']][df.UID.isin(uid)]
    ts['time'] = ts.tstamp.dt.time
    ts['date'] = ts.tstamp.dt.date
    ts['outside'] = ts['time'].where(ts['Loc']=='OUTSIDE')
    ts['inside'] = ts['time'].where(ts['Loc']=='INSIDE')    
    fig = plt.figure(figsize=(16, 7))
    plt.plot_date(ts.date[ts.inside.notnull()],ts.inside.dropna(), 'rv')
    plt.plot_date(ts.date[ts.outside.notnull()],ts.outside.dropna(), 'b^')
    fig.autofmt_xdate()
    return ts

"""        

#fig = plt.figure(figsize=(15, 10))
#plt.plot_date(df.date[ts.inside.notnull()],ts.inside.dropna(),  'ro')
#plt.plot_date(df.date[ts.outside.notnull()],ts.outside.dropna(),  'bo')
##fig.autofmt_xdate()
#plt.show()

