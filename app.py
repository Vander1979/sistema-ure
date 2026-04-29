import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. OBRIGATÓRIO: Primeiro comando do script
st.set_page_config(page_title="Rastreador URE Mogi", layout="wide")

# --- CONFIGURAÇÃO E BANCO DE DADOS ---
def conectar():
    return sqlite3.connect('protocolos_ure.db')

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS processos (
                        sei_id TEXT,
                        nome_lgpd TEXT,
                        cpf_mascarado TEXT,
                        cpf_busca TEXT,
                        assunto TEXT,
                        status_atual TEXT,
                        data_abertura TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historico_sei (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sei_id TEXT,
                        data_update TEXT,
                        status_novo TEXT,
                        obs TEXT)''')
    try:
        cursor.execute("SELECT cpf_busca FROM processos LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE processos ADD COLUMN cpf_busca TEXT")
    conn.commit()
    conn.close()

criar_tabelas()

# --- BARRA LATERAL E SENHA ---
st.sidebar.title("🔐 Acesso Restrito")
senha_servidor = st.sidebar.text_input("Senha do Servidor (URE)", type="password")
SENHA_CORRETA = "uremogi123" 

st.title("🏛️ Portal de Transparência - URE Mogi das Cruzes")

# --- LÓGICA DE EXIBIÇÃO DE ABAS ---
if senha_servidor == SENHA_CORRETA:
    abas = st.tabs(["🔍 Acompanhar Solicitação", "📥 Triagem (Entrada)", "⚙️ Atualização (Setores)"])
else:
    abas = st.tabs(["🔍 Acompanhar Solicitação"])
    st.sidebar.info("Área restrita a servidores da URE.")

# --- 1. VISÃO DO SOLICITANTE (Busca por CPF com Botão) ---
with abas[0]:
    st.subheader("Consulte o andamento pelo seu CPF")
    with st.container():
        busca_cpf = st.text_input("Digite seu CPF (apenas os 11 números)")
        botao_buscar = st.button("🔍 Buscar")
    
    if botao_buscar:
        if busca_cpf:
            cpf_usuario_limpo = "".join(filter(str.isdigit, busca_cpf))
            if len(cpf_usuario_limpo) == 11:
                conn = conectar()
                p = pd.read_sql(f"SELECT * FROM processos WHERE cpf_busca = '{cpf_usuario_limpo}'", conn)
                
                if not p.empty:
                    for index, row in p.iterrows():
                        with st.expander(f"📌 Processo: {row['sei_id']} - {row['assunto']}"):
                            col_a, col_b = st.columns(2)
                            col_a.write(f"**Solicitante:** {row['nome_lgpd']}")
                            col_a.write(f"**CPF:** {row['cpf_mascarado']}")
                            col_b.metric("Status Atual", row['status_atual'])
                            st.write("---")
                            st.write("**Histórico de Movimentações:**")
                            h = pd.read_sql(f"SELECT data_update as Data, status_novo as Status, obs as Detalhes FROM historico_sei WHERE sei_id = '{row['sei_id']}' ORDER BY id DESC", conn)
                            st.table(h)
                else:
                    st.warning("Nenhum registro encontrado para este CPF.")
                conn.close()
            else:
                st.error("O CPF deve conter exatamente 11 números.")
        else:
            st.warning("Por favor, digite um CPF para buscar.")

# --- 2. VISÃO TRIAGEM ---
if senha_servidor == SENHA_CORRETA:
    with abas[1]:
        st.subheader("📥 Cadastrar Novo Atendimento")
        with st.form("cadastro_sei", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                num_sei = st.text_input("Número do SEI (ou 'Aguardando')")
                nome_completo = st.text_input("Nome Completo")
            with c2:
                cpf_input = st.text_input("CPF (Somente números)")
                assunto = st.selectbox("Assunto", ["Equipamentos", "Manutenção", "RH", "Documentação", "Financeiro"])
            obs_inicial = st.text_area("Observação/Descrição")
            
            if st.form_submit_button("Lançar no Sistema"):
                if nome_completo and cpf_input:
                    primeiro_nome = nome_completo.split()[0].upper()
                    cpf_limpo = "".join(filter(str.isdigit, cpf_input))
                    if len(cpf_limpo) == 11:
                        cpf_mask = f"{cpf_limpo[:3]}.***.***-{cpf_limpo[9:]}"
                        data_agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                        conn = conectar()
                        try:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO processos (sei_id, nome_lgpd, cpf_mascarado, cpf_busca, assunto, status_atual, data_abertura) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                           (num_sei, primeiro_nome, cpf_mask, cpf_limpo, assunto, "Enviado ao Setor Responsável", data_agora))
                            cursor.execute("INSERT INTO historico_sei (sei_id, data_update, status_novo, obs) VALUES (?, ?, ?, ?)",
                                           (num_sei, data_agora, "Enviado ao Setor Responsável", obs_inicial))
                            conn.commit()
                            st.success(f"✅ Protocolo registrado para {primeiro_nome}!")
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
                        finally:
                            conn.close()
                    else:
                        st.error("CPF inválido.")

    # --- 3. VISÃO SETORES (Feedback de Sucesso) ---
    with abas[2]:
        st.subheader("⚙️ Atualizar Status")
        conn = conectar()
        lista_df = pd.read_sql("SELECT sei_id, nome_lgpd FROM processos WHERE status_atual != 'Finalizado'", conn)
        
        if not lista_df.empty:
            opcoes = lista_df.apply(lambda x: f"{x['sei_id']} - {x['nome_lgpd']}", axis=1)
            escolha = st.selectbox("Selecione o processo", opcoes)
            sei_selecionado = escolha.split(" - ")[0]
            novo_status = st.selectbox("Novo Status", ["Recebido pelo Setor", "Em Análise Técnica", "Aguardando Documentação", "Finalizado"])
            detalhes = st.text_area("Informações da atualização")
            
            if st.button("Confirmar Atualização"):
                data_up = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor = conn.cursor()
                cursor.execute("UPDATE processos SET status_atual = ? WHERE sei_id = ?", (novo_status, sei_selecionado))
                cursor.execute("INSERT INTO historico_sei (sei_id, data_update, status_novo, obs) VALUES (?, ?, ?, ?)",
                               (sei_selecionado, data_up, novo_status, detalhes))
                conn.commit()
                st.success("✅ Status atualizado com sucesso!")
                # Pequeno delay para o usuário ver a mensagem antes de atualizar a lista
                st.balloons()
        else:
            st.info("Nenhum processo pendente.")
        conn.close()
