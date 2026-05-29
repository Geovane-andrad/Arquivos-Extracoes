


import psycopg2


user = 'setup-bi'
host = 'valorem-bi.cv78gjbuoavo.us-east-1.rds.amazonaws.com'
port = '5432'
database = 'db_datalake'


try:

    conn = psycopg2.connect( 
    database=database, 
    user=user,  
    password='B1v@lorem,23!code:j8`<Pf?Lzh`&iRmC^86%',  
    host=host,  
    port=port
    ) 
    status_banco = 1

except Exception as error:
    print ("Oops! An exception has occured:", error)
    print ("Exception TYPE:", type(error))
    status_banco = 0











