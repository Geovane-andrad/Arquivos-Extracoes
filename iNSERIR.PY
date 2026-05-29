import pandas as pd
import sys_conexaoBanco as cnx
import numpy as np

def inserir_dados():
    try:
        print("="*50)
        print("🚀 INICIANDO PROCESSO DE INSERÇÃO")
        print("="*50)
        
        # 1. LER ARQUIVO
        print("\n📖 PASSO 1: Lendo arquivo Excel...")
        caminho = r"C:\Users\geovane.andrade\Downloads\Inserir registros\Metas despesas 2026 - v2.xlsx"
        df = pd.read_excel(caminho)
        print(f"   ✅ Arquivo lido: {df.shape[0]} linhas, {df.shape[1]} colunas")
        
        # 2. RENOMEAR COLUNAS
        print("\n📝 PASSO 2: Renomeando colunas...")
        df.rename(columns={
            'ano': 'nr_ano',
            'mês': 'nr_mes',
            'cd centro custo': 'cd_centro_custo',
            'id conta': 'id_conta',
            'id empresa': 'id_empresa_jb',
            'vl orcamento': 'vl_orcamento'
        }, inplace=True)
        print(f"   ✅ Colunas renomeadas: {list(df.columns)}")
        
        # 3. SELECIONAR COLUNAS
        print("\n✂️ PASSO 3: Selecionando colunas necessárias...")
        df = df[['nr_ano', 'nr_mes', 'cd_centro_custo', 'id_conta', 'id_empresa_jb', 'vl_orcamento']]
        print(f"   ✅ Colunas selecionadas: {list(df.columns)}")
        
        # 4. TRATAR VALORES NULOS
        print("\n🧹 PASSO 4: Tratando valores nulos...")
        df = df.replace({np.nan: None})
        print(f"   ✅ Valores nulos tratados")
        
        # 5. INSERIR NO BANCO
        print("\n💾 PASSO 5: Inserindo no banco de dados...")
        with cnx.conn.cursor() as cursor:
            contador = 0
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO public.atualizar_despesas_jb 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    row['nr_ano'], row['nr_mes'], row['cd_centro_custo'],
                    row['id_conta'], row['id_empresa_jb'], row['vl_orcamento']
                ))
                contador += 1
                if contador % 1000 == 0:
                    print(f"   ➜ {contador} registros inseridos...")
            
            cnx.conn.commit()
            
        print(f"\n✅ PASSO 6: FINALIZADO - {contador} registros inseridos com sucesso!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        cnx.conn.rollback()
        print("="*50)

# EXECUTAR
if __name__ == "__main__":
    inserir_dados()