import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Rastreador URE Mogi", layout="wide")

# 2. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

# --- BARRA LATERAL E SENHA ---
st.sidebar.title("🔐 Acesso Restrito")
senha_servidor = st.sidebar.text_input("Senha do Servidor (URE)", type="password")
SENHA_CORRETA = "uremogi123" # Altere aqui

st.title("🏛️ Portal de Transparência - URE Mogi das Cruzes")

if senha_servidor == SENHA_CORRETA:
    abas = st.tabs(["🔍 Acompanhar Solicitação", "📥 Triagem", "⚙️ Atualização"])
else:
    abas = st.tabs(["🔍 Acompanhar Solicitação"])
    st.sidebar.info("Área restrita a servidores.")

# --- 1. CONSULTA (PÚBLICA) ---
with abas[0]:
    st.subheader("Consulte pelo seu CPF")
    busca_cpf = st.text_input("Digite seu CPF (apenas números)")
    if st.button("🔍 Buscar"):
        cpf_limpo = "".join(filter(str.isdigit, busca_cpf))
        if len(cpf_limpo) == 11:
            # Lê a aba principal da planilha
            df_processos = conn.read(worksheet="Sheet1") # Ajuste o nome da aba se necessário
            p = df_processos[df_processos['cpf_busca'].astype(str) == cpf_limpo]
            
            if not p.empty:
                for _, row in p.iterrows():
                    with st.expander(f"📌 {row['sei_id']} - {row['assunto']}"):
                        st.info(f"**Solicitante:** {row['nome_lgpd']} | **Status:** {row['status_atual']}")
                        # Busca histórico na outra aba
                        df_hist = conn.read(worksheet="historico")
                        h = df_hist[df_hist['sei_id'] == row['sei_id']]
                        st.table(h[['data_update', 'status_novo', 'obs']])
            else:
                st.warning("Nenhum registro encontrado.")
        else:
            st.error("CPF inválido.")

# --- 2. TRIAGEM (COM SENHA) ---
if senha_servidor == SENHA_CORRETA:
    with abas[1]:
        with st.form("cadastro"):
            sei = st.text_input("Número SEI")
            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF")
            assunto = st.selectbox("Assunto", ["Equipamentos", "Manutenção", "RH", "Financeiro"])
            if st.form_submit_button("Lançar"):
                # Lógica para salvar no Google Sheets
                df_processos = conn.read(worksheet="Sheet1")
                # Aqui o código para adicionar nova linha e conn.update()
                st.success("Cadastrado! (Ajustaremos a escrita após o deploy)")

# --- 3. ATUALIZAÇÃO (COM SENHA) ---
# Lógica similar para dar update na planilha
