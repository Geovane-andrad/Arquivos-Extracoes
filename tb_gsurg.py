import os
import json

# Caminho da pasta User.zip (ajuste se necessário)
caminho_zip = r"C:\Users\geovane.andrade\AppData\Local\Microsoft\Power BI Desktop"
caminho_temp = r"C:\Users\geovane.andrade\Documents"

# Cria pasta temporária se não existir
os.makedirs(os.path.join(caminho_temp, "UserInterface"), exist_ok=True)

# Conteúdo do arquivo Options.json
conteudo = {
    "EnableConnectionStringView": True
}

# Caminho final do arquivo JSON
caminho_arquivo = os.path.join(caminho_temp, "UserInterface", "Options.json")

# Escreve o arquivo
with open(caminho_arquivo, "w") as f:
    json.dump(conteudo, f, indent=4)

print(f"Arquivo Options.json criado em: {caminho_arquivo}")
print("Agora, substitua a pasta 'UserInterface' dentro do 'User.zip' pelo conteúdo criado.")
