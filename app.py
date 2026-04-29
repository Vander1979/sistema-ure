import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
# 1. Cole aqui o link de "Publicar na Web" (CSV) para leitura rápida
URL_LEITURA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPIQHHCmZ9LZvPoOCtB5OZWrdaYo2JMLkEdA41kyCPl6QkOicagxu-U7vQxSH9kNEeISvueqqI94UK/pub?output=csv"
# 2. Cole aqui o URL do Script que você acabou de criar
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbxw-J7-h69crq-LbHp26zf0XHrlKoBOFsbc6xWUmghn762GF7MNKU-LqFa1JBHo-cst/exec"

st.set_page_config(page_title="Rastreador URE Mogi", layout="wide")

# Interface
st.sidebar.title("🔐 Acesso Restrito")
senha = st.sidebar.text_input("Senha do Servidor", type="password")
SENHA_CORRETA = "uremogi123"

st.title("🏛️ Portal de Transparência - URE Mogi das Cruzes")

# RECUPERANDO AS ABAS
if senha == SENHA_CORRETA:
    abas = st.tabs(["🔍 Consulta", "📥 Triagem", "⚙️ Atualização"])
else:
    abas = st.tabs(["🔍 Consulta"])

# --- ABA 1: CONSULTA ---
with abas[0]:
    busca_cpf = st.text_input("Consultar por CPF")
    if st.button("Buscar"):
        df = pd.read_csv(URL_LEITURA)
        res = df[df['cpf_busca'].astype(str).str.contains(busca_cpf)]
        if not res.empty:
            for _, r in res.iterrows():
                with st.expander(f"SEI {r['sei_id']}"):
                    st.write(f"Status: {r['status_atual']}")
        else: st.warning("Não encontrado.")

# --- ABA 2: TRIAGEM (CADASTRO) ---
if senha == SENHA_CORRETA:
    with abas[1]:
        with st.form("form_cad"):
            sei = st.text_input("Número SEI")
            nome = st.text_input("Nome")
            cpf = st.text_input("CPF (11 dígitos)")
            assunto = st.selectbox("Assunto", ["TI", "RH", "Obras", "Outros"])
            if st.form_submit_button("Lançar no Sistema"):
                data_agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                mask = f"{cpf[:3]}.***.***-{cpf[9:]}"
                # Enviando para a planilha via Script
                payload = {"tipo": "cadastro", "sei": sei, "nome": nome.split()[0].upper(), "mask": mask, "cpf": cpf, "assunto": assunto, "data": data_agora, "obs": "Cadastro Inicial"}
                requests.post(URL_SCRIPT, json=payload)
                st.success("✅ Protocolo registrado!")

# --- ABA 3: ATUALIZAÇÃO ---
with abas[len(abas)-1] if senha == SENHA_CORRETA else abas[0]:
    if senha == SENHA_CORRETA:
        st.subheader("Atualizar Status")
        # Aqui você pode ler a planilha e mudar o status
        st.write("Selecione o processo na planilha para alterar o status.")
