import streamlit as st
import pandas as pd
from datetime import datetime

# 1. LINKS DA PLANILHA (Substitua pelos links que você copiou agora)
# DICA: O link deve terminar com 'output=csv'
URL_DADOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPIQHHCmZ9LZvPoOCtB5OZWrdaYo2JMLkEdA41kyCPl6QkOicagxu-U7vQxSH9kNEeISvueqqI94UK/pub?output=csv"
URL_HISTORICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPIQHHCmZ9LZvPoOCtB5OZWrdaYo2JMLkEdA41kyCPl6QkOicagxu-U7vQxSH9kNEeISvueqqI94UK/pub?gid=186597890&single=true&output=csv"

st.set_page_config(page_title="Rastreador URE Mogi", layout="wide")

# FUNÇÃO PARA LER OS DADOS SEM ERRO
def carregar(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# --- INTERFACE ---
st.sidebar.title("🔐 Acesso Restrito")
senha = st.sidebar.text_input("Senha do Servidor", type="password")
SENHA_CORRETA = "uremogi123"

st.title("🏛️ Portal de Transparência - URE Mogi das Cruzes")

if senha == SENHA_CORRETA:
    abas = st.tabs(["🔍 Consulta", "📥 Cadastro"])
else:
    abas = st.tabs(["🔍 Consulta"])

# --- ABA DE CONSULTA ---
with abas[0]:
    busca_cpf = st.text_input("Digite o CPF para consultar")
    if st.button("🔍 Buscar"):
        df = carregar(URL_DADOS)
        if not df.empty:
            # Filtra removendo pontos e traços do CPF digitado e da base
            cpf_alvo = "".join(filter(str.isdigit, busca_cpf))
            res = df[df['cpf_busca'].astype(str).str.contains(cpf_alvo)]
            
            if not res.empty:
                for _, row in res.iterrows():
                    with st.expander(f"📌 SEI: {row['sei_id']} - {row['assunto']}"):
                        st.write(f"**Status:** {row['status_atual']}")
                        st.write(f"**Última Atualização:** {row['data_abertura']}")
            else:
                st.warning("Nenhum registro encontrado.")
        else:
            st.error("Erro ao ler a base de dados. Verifique a publicação da planilha.")

# --- ABA DE CADASTRO (Aviso técnico) ---
if senha == SENHA_CORRETA:
    with abas[1]:
        st.info("💡 Como estamos usando o modo 'Publicar na Web', a gravação direta pelo site é restrita. Para lançar novos dados, alimente a planilha diretamente no Google Drive. O site atualizará automaticamente em alguns segundos.")
