# -*- coding: utf-8 -*-
"""
Created on Mon Jul 06 13:28:10 2015

@author: Efrem
"""

# This is the file that I originally wanted to distribute to the HUB staff as an executable, 
#  but I could not get that to work with Nuitka, PyInstall, nor py2exe.

from HUB_access import *
import tkFileDialog


def main():
    file_list = tkFileDialog.askopenfilenames(title='Choose report file(s)',filetypes=[('Text file','*.txt')])
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
    df2.to_csv('output.csv', index=False, float_format='%2.3f')
    
    df2 = factor_datetime_index(df2)    
    df_user = df2.sort(['UID','tstamp']).set_index(['UID','Name','Year','Date','Day','Time'])[['tstamp','Loc','Period']]
    df_user['tstamp'] = df_user.tstamp.map(lambda x:x.strftime('%Y/%m/%d %H:%M') )
    df_user.to_excel('output_grouped.xls',float_format='%2.3f')

    
    
if __name__ == "__main__":
    main()
    
