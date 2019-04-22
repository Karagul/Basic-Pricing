'''
Created on May 17, 2017

@author: ACM04 - Ning
@Comments: This module would provide basic functionality for execute db queries
'''
import pymysql
import DB.initialdbLogin as login

def dbExecute( schema_name, 
               sqlstring,
               storedProcParameters = None ):
    
    dblogin = login.initialDBLogin( schema_name )
    hostip = dblogin['ip']
    dbname = dblogin['dbname']
    pwd = dblogin['pw']
    userid = dblogin['userid']

    conn = pymysql.connect( host = hostip, 
                            user = userid, 
                            password = pwd, 
                            db   = dbname,
                            charset  = 'utf8mb4', 
                            cursorclass  = \
                            pymysql.cursors.DictCursor,
                            autocommit   = True,
                            local_infile = 1)
    cc = conn.cursor()
    
    if storedProcParameters == None:
        cc.execute( sqlstring )
    else:
        cc.callproc( sqlstring,
                     storedProcParameters )
    conn.commit()
    
    resultDataset = cc.fetchall()
    
    return resultDataset
