# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:48:54 2015

@author: Efrem
"""
   
# This script reads a txt file containing an Integra Link events report      
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

# Read in a report from a text file output by Integra Link   
def from_txt(file_name):    
    # in this file there should be three columns: Date, Time, and Event
    #   but we can expect them to be mixed up.

    #  Line by line:
    #    Let F be first non-empty position in line       
    #    If F  is date in MM/DD/YYYY form
    #       set DATE to that date 
    #    else if F is a time of day
    #       set TOD to that time
    #       Concatenate the rest of that line into EVENT
    #    else skip that line
    #
    #    construct a row as [DATE, TOD, EVENT]
    print('Reading "%s"...') % file_name
    f = open(file_name,'r')
    file_struct = f.readlines()
    f.close()
    
    datetimestamps = []
    events = []  
      
    for line in file_struct:
        line = line.strip()
        if line: # if cell is not empty
            row = line.split()
            first_token =  row[0]
            try:
                datestamp = dt.datetime.strptime(first_token, '%m/%d/%Y').date()
            except ValueError:
                first_two_tokens = " ".join(row[:2])
                try:
                    timestamp = dt.datetime.strptime(first_two_tokens, '%I:%M %p').time()
                    event = ' '.join(row[2:])
                    datetimestamps.append(dt.datetime.combine(datestamp,timestamp))
                    events.append(event)
                except ValueError:
                    pass
    
    df = pd.DataFrame({ 'Timestamp' : datetimestamps, 'Event' : events })
    df = df.drop_duplicates()
    df = df.set_index('Timestamp')
    df = df.sort_index()
    
    return df


def Door_Access_report(df,hour_offset=0):
    df.index += pd.DateOffset(hours=hour_offset)
    ## Extract door data 
    ddata = df[df.Event.str.startswith('Door')]
    denied = ddata.Event.str.contains('Denied')
    
    Access = ddata[~denied]
    Access = Access.sort_index()
    temp = Access.Event.str.split(': ')
    Access = Access.drop('Event',axis=1)
    
    UID, Name = temp.str[2].str.split(' ',1).str
    Action = temp.str[1].str.split(' ',2).str[1]
    
    Access['Loc'] = Action.map( {'ENTRY': 'OUTSIDE', 'EXIT': 'INSIDE'} ).astype("category")
    Access["Loc"].cat.set_categories(["INSIDE","OUTSIDE"],inplace=True)


#    Access['When'] = [x.strftime('%a %m-%d, %I:%M %p') for x in Access.index]
    Access['UID'] = UID.astype(int)
    Access['Name'] = Name.str.title()
    
    return Access 
    
  
def factor_datetime_index(df):
    ts = df.tstamp
    df['Day'] = [x.strftime('%a') for x in ts]
    df['Date'] = [x.strftime('%m-%d') for x in ts]
    df['Time'] = [x.strftime('%I:%M %p') for x in ts]
    df['Week#'] = ts.dt.week
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
    period = df[check==1]['time_delta'].dt
    df['Period'] = 24*period.days + period.hours + (period.minutes/60.0).round(2)
    
    # Disregard any period of over 18 hours, which is silly
    df.loc[df['Period'] > 18, 'Period'] = None    
    df = df.drop('time_delta',axis=1)
 
    return df


    


# ************** Main Code ********************

pd.set_option('expand_frame_repr', False)

#r2 = Door_Access_report(from_txt('HUB_Door_Report_2_2015.txt'),+1)['2/2015']
#r3 = Door_Access_report(from_txt('HUB_Door_Report_3_2015.txt'))['3/2015']
#r4 = Door_Access_report(from_txt('HUB_Door_Report_4_2015.txt'))['4/2015']
#r5 = Door_Access_report(from_txt('HUB_Door_Report_5_2015.txt'))
#
#r_all = pd.concat([r2,r3,r4,r5]).sort_index()
#r_all.to_csv('HUB_Door_all.csv')

r = pd.read_csv('HUB_Door_all.csv', names=['tstamp','Loc','UID','Name'], skiprows=[0])
r.tstamp = pd.to_datetime(r.tstamp)
r.Loc = r.Loc.astype('category')
r.UID = r.UID.astype(int)

UIDs = r[['UID','Name']].drop_duplicates().set_index('UID')
def UID(name):
    return UIDs[UIDs.Name.str.contains(name,case=False)]


r = make_durations(r)

print('%d unique user IDs') % len(r.UID.unique())

df = factor_datetime_index(r)

# First we rearrange data into time series columns for each user
ts = pd.pivot_table(df, index=['tstamp'],columns=['UID'],values='Loc',aggfunc='last')

# Next we resample time series to one day intervals and indicate whether a user swiped a card that day
ts_days = ts.resample('D', how='count').astype(bool)
ts_days.sum(axis=1).plot(figsize=(15,5),title='total accesses by day')

dpw = ts_days.resample('W-Mon', how='sum')


#day_sum = ru.groupby(['UID','Date'])['Period'].sum()
#week_sum = ru.groupby(['UID','Week#'])['Period'].sum()
#total_sum = ru.groupby(['UID'])['Period'].sum()


"""
#plot total hours by day
#pd.pivot_table(r, index=['Date','Day'], values='Period',aggfunc=pd.np.sum).plot(kind='bar',figsize=(16,5))
r.groupby(['Date','Day'])['Period'].sum().plot(kind='bar',figsize=(16,5))


# This is a summary of door accesses by user
r3us = r3u[['UID','Name','Week#','Day','Date','Time','Loc','Period']].set_index(['UID','Name','Week#','Day','Date','Time'])
#r3us.to_excel('Door_User_summary_3-2015.xlsx')


# This pivot-table has weekly totals for every active member over every active day in the period
r3w = pd.pivot_table(r3u,index='UID', columns=['Week#'], values='Period', margins=True, aggfunc=pd.np.sum)
r3w = r3w.dropna(axis=0, how='all')  # drop empty rows (people with no determined hours)
#r3w.to_excel('Door_Weekly_totals_3-2015.xlsx')


# This pivot-table has daily totals for every active member over every active day in the period
r3d = pd.pivot_table(r3u,index='UID', columns=['Week#','Date'], values='Period', margins=True, aggfunc=pd.np.sum)
r3d = r3d.dropna(axis=0, how='all')  # drop empty rows (people with no determined hours)
#r3d.to_excel('Door_Daily_totals_3-2015.xlsx')

II


day_sum = r3u['Period'].groupby(level=['UID','Date']).transform(sum)
total_sum = r3u['Period'].groupby(level=['UID','Name']).transform(sum)
"""

def explore_user(uid):
    ts = df[['tstamp','Loc']][df.UID==uid].set_index('tstamp')
    ts['hour'] = ts.index.hour + (ts.index.minute / 60.0)
    ts['outside'] = ts['hour'].where(ts['Loc']=='OUTSIDE')
    ts['inside'] = ts['hour'].where(ts['Loc']=='INSIDE')
    ts = ts.set_index(ts.index.date).drop('Loc',axis=1)
    ts[['inside','outside']].plot(style='o',figsize=(16,7),title='Entry/Exit for user #%d'%uid)
    ts['weekday'] = [x.strftime('%a') for x in ts.index]
    return ts.drop('hour',axis=1)

