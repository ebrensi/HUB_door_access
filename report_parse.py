# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 17:48:54 2015

@author: Efrem
"""
# this script takes text files given on the command line and parses them into a csv file
#  Note: this is what I finally settled on to give to the HUB for processing their 
#    card-reader data.   Nuitka compiles this code fine, but for some reason cannot handle
#    the Pandas module.  I did not have a lot of time to get it to work with Pandas, so this 
#    was my Pandas-free alternative.

import sys
import re

def parse_text_report(files, outfile='output.csv'):
    p_date = re.compile('^\s*(\d+/\d+/\d+)') # this is the format for dates
    e_date = re.compile('(\d+)/(\d+)/(\d+)') # this is for extracting the date
    
    p_user = re.compile('^\s*(\d+:\d+ [AP]M) .* (ENTRY|EXIT) READER .* User: (\d+) (.*) ')
    e_time = re.compile('(\d+):(\d+) ([AP]M)')
    action2loc = {'ENTRY': 'OUTSIDE', 'EXIT': 'INSIDE'}
    
    fields = ['UID','Name','Year','Date','Time','tstamp','Loc']

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
    with open(outfile, 'w') as csvfile:
        csvfile.write(','.join(fields) + '\n')
        for text_file in files:
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
                            date_only = month.zfill(2) + '-' + day.zfill(2)
                            date.append(date_only)
                            time.append(time12)
                            ts = yyyymmdd + ' ' + time24
                            tstamp.append(ts)
                            l = action2loc[loc_in]
                            loc.append(l)
                            uid.append(uid_in)
                            name.append(name_in)  
                            # fields = ['UID','Name','Year','Date','Time','tstamp','Loc']
                            csvfile.write(','.join([uid_in, name_in, yr, date_only, time12, ts, l])+'\n')
                

    
parse_text_report(sys.argv[1:])


        