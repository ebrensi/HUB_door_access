# This is an attempt at making a version of my little parser app that can be compiled by Nuitka, which seems to 
#  have a problem with Pandas.

from HUB_access import *
 
file_list = ['HUB_Door_Report_2_2015.txt','HUB_Door_Report_3_2015.txt',
             'HUB_Door_Report_4_2015.txt','HUB_Door_Report_5_2015.txt']
dfs = []
for f in file_list:
    try:
        df = import_txt_report(f)
    except:
        df = []
              
    dfs.append(df)

df1 = pd.concat(dfs)
df2 = Door_Access_report(df1).reset_index()
df2 = make_durations(df2).sort('tstamp')
df2.to_csv('output.csv',ignore_index=True)

df2 = factor_datetime_index(df2)
df_user = df2.sort('UID').set_index(['UID','Name','Date','Day','Time'])[['Loc','Period']]

df_user.to_excel('output_grouped.xls')
