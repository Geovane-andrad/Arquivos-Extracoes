

import psycopg2


def fn_inserirLog(conn, funcao ,pid, script, projeto, etapa, parametro,  ex_erro): 

	# SQL query to execute 

	if funcao == 'iniciar':
		query = "call privated.sp_atualizalog_script('iniciar',"+pid+","+script+","+projeto+","+etapa+","+parametro+",null)"

	if funcao == 'parametrizar':
		query = "call privated.sp_atualizalog_script('parametrizar',"+pid+","+script+","+projeto+","+etapa+","+parametro+",null)"

	if funcao == 'finalizar':
		query = "call privated.sp_atualizalog_script('finalizar',"+pid+","+script+","+projeto+","+etapa+","+parametro+",null)"

	if funcao == 'dfVazio':
		query = "call privated.sp_atualizalog_script('finalizar',"+pid+","+script+","+projeto+","+etapa+","+parametro+",null)"

	if funcao == 'error':
		query = "call privated.sp_atualizalog_script('error',"+pid+","+script+","+projeto+","+etapa+","+parametro+",'"+str(ex_erro).replace("'","")+"')"


	print(query)
	cursor = conn.cursor() 
    
	try: 
		cursor.execute(query)
		conn.commit() 
	except (Exception, psycopg2.DatabaseError) as error: 
		print("-> Erro: %s" % error) 
		conn.rollback() 
		cursor.close() 
		return 1
	print("-> Log registrado!") 
	cursor.close() 

