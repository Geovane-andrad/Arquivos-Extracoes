

import sys_conexaoBanco
import psycopg2
import psycopg2.extras as extras 


def fn_inserirRegistros(conn, df, table): 

	query_delete = 'delete from '+table
	tuples = [tuple(x) for x in df.to_numpy()] 
	cols = ', '.join(list(df.columns)) 
	# SQL query to execute 
	query = 'INSERT INTO %s(%s) VALUES ' % (table, cols) 
	cursor = conn.cursor() 
    
	try:
		cursor.execute(query_delete)
		conn.commit()
		print('')
		print('-> Limpeza da tabela realizada!')

		inicio=0
		fim = 0
		print(len(tuples))

		while fim < len(tuples):

			inicio = fim 
			fim = fim+1000
			valores = str(tuples[inicio:fim])
			valores_inserir = valores.replace("'null'","null").replace('[','').replace(']','').replace("'None'","null").replace("'nan'","null").replace("None,","null,").replace("nan,","null,").replace("None)","null)").replace("nan)","null)")
			##print(nova_tupla)
			
			falta = len(tuples)-fim
			if falta < 0: falta = 0
			print("inserindo range de: "+str(inicio)+" até: "+str(fim))
			print("faltam "+str(falta)+" registros")

			valores = str(tuples)
			##print(query+valores_inserir)
			cursor.execute(query+valores_inserir)
			conn.commit()
	
		
		##extras.execute_values(cursor, query, tuples) 
 
	except (Exception, psycopg2.DatabaseError) as error:
		print("-> Erro: %s" % error)
		conn.rollback()
		cursor.execute(query_delete)
		cursor.close()
		exit(1)
		return 1
	
	print('')
	print("-> O Dataframe foi inserido na tabela destino!") 
	cursor.close() 