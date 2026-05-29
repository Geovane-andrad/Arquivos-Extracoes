

import pandas as pd
import html
from bs4 import BeautifulSoup

def limpar_html(texto):
    if pd.isna(texto):  # Evita erro caso tenha valores nulos
        return ""
    
    # Remove tags HTML
    texto_sem_tags = BeautifulSoup(texto, "html.parser").get_text()
    
    # Converte entidades HTML (&ccedil; -> ç, &atilde; -> ã, etc.)
    texto_convertido = html.unescape(texto_sem_tags)
    
    # Substitui caracteres indesejados (\xa0 )
    texto_final1 = texto_convertido.replace('\xa0', ' ').strip()

    # Substitui caracteres indesejados (\n)
    texto_final2 = texto_final1.replace('\n', ' ').strip()

    # Substitui caracteres indesejados (\r)
    texto_final3 = texto_final2.replace('\r', ' ').strip()

    # Substitui caracteres indesejados (\t)
    texto_final4 = texto_final3.replace('\t', '').strip()
    
    return texto_final4


def remove_quotes(df, column_name):
    """
    Remove aspas simples e duplas de todos os valores de uma coluna específica de um DataFrame.
    
    :param df: DataFrame do pandas
    :param column_name: Nome da coluna onde as aspas serão removidas
    :return: DataFrame com a coluna modificada
    """
    df[column_name] = df[column_name].astype(str).str.replace(r"[\"']", "", regex=True)
    return df
