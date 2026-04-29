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
SENHA_CORRETA = "uremogi123" 

st.title("🏛️ Portal de Transparência - URE Mogi das Cruzes")

# LÓGICA DE ABAS
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
            df_processos = conn.read(worksheet="Sheet1")
            p = df_processos[df_processos['cpf_busca'].astype(str) == cpf_limpo]
            
            if not p.empty:
                for _, row in p.iterrows():
                    with st.expander(f"📌 {row['sei_id']} - {row['assunto']}"):
                        st.info(f"**Solicitante:** {row['nome_lgpd']} | **Status Atual:** {row['status_atual']}")
                        try:
                            df_hist = conn.read(worksheet="historico")
                            h = df_hist[df_hist['sei_id'] == row['sei_id']]
                            st.table(h[['data_update', 'status_novo', 'obs']])
                        except:
                            st.write("Sem histórico disponível.")
            else:
                st.warning("Nenhum registro encontrado para este CPF.")
        else:
            st.error("Digite os 11 números do CPF.")

# --- 2. TRIAGEM (CADASTRO) ---
if senha_servidor == SENHA_CORRETA:
    with abas[1]:
        st.subheader("📥 Novo Atendimento")
        with st.form("cadastro_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                sei = st.text_input("Número SEI")
                nome = st.text_input("Nome Solicitante")
            with col2:
                cpf_input = st.text_input("CPF (11 números)")
                assunto = st.selectbox("Assunto", ["Equipamentos", "Manutenção", "RH", "Financeiro"])
            obs = st.text_area("Observação inicial")
            
            if st.form_submit_button("Lançar no Sistema"):
                cpf_limpo = "".join(filter(str.isdigit(cpf_input)))
                if len(cpf_limpo) == 11:
                    # Preparar dados
                    data_at = datetime.now().strftime("%d/%m/%Y %H:%M")
                    mask = f"{cpf_limpo[:3]}.***.***-{cpf_limpo[9:]}"
                    
                    # Atualizar Planilha Principal
                    df_base = conn.read(worksheet="Sheet1")
                    novo_dado = pd.DataFrame([{
                        "sei_id": sei, "nome_lgpd": nome.split()[0].upper(),
                        "cpf_mascarado": mask, "cpf_busca": cpf_limpo,
                        "assunto": assunto, "status_atual": "Recebido", "data_abertura": data_at
                    }])
                    df_final = pd.concat([df_base, novo_dado], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=df_final)
                    
                    # Atualizar Histórico
                    df_h = conn.read(worksheet="historico")
                    novo_h = pd.DataFrame([{"sei_id": sei, "data_update": data_at, "status_novo": "Recebido", "obs": obs}])
                    df_h_final = pd.concat([df_h, novo_h], ignore_index=True)
                    conn.update(worksheet="historico", data=df_h_final)
                    
                    st.success("✅ Protocolo cadastrado com sucesso!")
                else:
                    st.error("CPF inválido.")

# --- 3. ATUALIZAÇÃO ---
if senha_servidor == SENHA_CORRETA:
    with abas[2]:
        st.subheader("⚙️ Atualizar Status")
        df_base = conn.read(worksheet="Sheet1")
        if not df_base.empty:
            escolha = st.selectbox("Selecione o Processo", df_base['sei_id'].tolist())
            novo_status = st.selectbox("Novo Status", ["Em Análise", "Aguardando Doc", "Finalizado"])
            detalhes = st.text_area("Detalhes da atualização")
            
            if st.button("Confirmar Atualização"):
                data_at = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Update na principal
                df_base.loc[df_base['sei_id'] == escolha, 'status_atual'] = novo_status
                conn.update(worksheet="Sheet1", data=df_base)
                
                # Add no histórico
                df_h = conn.read(worksheet="historico")
                novo_h = pd.DataFrame([{"sei_id": escolha, "data_update": data_at, "status_novo": novo_status, "obs": detalhes}])
                df_h_final = pd.concat([df_h, novo_h], ignore_index=True)
                conn.update(worksheet="historico", data=df_h_final)
                
                st.success("✅ Status atualizado!")
                st.balloons()
