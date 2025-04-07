import streamlit as st
import datetime
import json
import os
from datetime import timedelta

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase/firebase_config_py.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Configurações da página
st.set_page_config(
    page_title="VOLEIZINHO PRA CURAR ONDE DÓI",
    page_icon=":volleyball:"
)

# Configurações iniciais
data_file = "volei_agenda.json"
quadras_file = "volei_quadras.json"
QUADRAS_DISPONIVEIS = ["11", "12", "13", "14", "15", "16", "17", "18", "19", "24", "25", "26"]

# Dias da semana fixos
DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

# Estrutura padrão para cada dia
DIA_ESTRUTURA = {
    'Titulares': [],
    'Reservas': [],
    'Substitutos': [],
    'Quadra': None
}

# Funções de carregamento/salvamento
# def load_data():
#     if os.path.exists(data_file):
#         with open(data_file, "r") as f:
#             data = json.load(f)
#             # Garante que todos os dias estão presentes
#             for dia in DIAS_SEMANA:
#                 if dia not in data:
#                     data[dia] = DIA_ESTRUTURA.copy()
#             return data
#     return {}
#
# def save_data(data):
#     with open(data_file, "w") as f:
#         json.dump(data, f, indent=4)

def save_data(data):
    for dia, info in data.items():
        doc_ref = db.collection("agenda").document(dia)
        doc_ref.set(info)

def load_data():
    docs = db.collection("agenda").stream()
    agenda = {}
    for doc in docs:
        data = doc.to_dict()
        data["Titulares"] = sorted(data.get("Titulares", []))
        data["Reservas"] = sorted(data.get("Reservas", []))
        data["Substitutos"] = sorted(data.get("Substitutos", []))
        agenda[doc.id] = data
    return agenda

def load_quadras():
    if os.path.exists(quadras_file):
        with open(quadras_file, "r") as f:
            return json.load(f)
    return {}

def save_quadras(data):
    with open(quadras_file, "w") as f:
        json.dump(data, f, indent=4)

# Função para verificar se precisa resetar (domingo após 19h)
def should_reset():
    now = datetime.datetime.now()
    if now.weekday() == 6 and now.hour >= 19:
        last_reset_file = "last_reset_date.txt"
        today_date = now.date().isoformat()
        
        if os.path.exists(last_reset_file):
            with open(last_reset_file, "r") as f:
                last_reset = f.read().strip()
            if last_reset == today_date:
                return False
        
        with open(last_reset_file, "w") as f:
            f.write(today_date)
        return True
    return False

# Função para resetar os dados
def reset_week_data():
    st.session_state.volei_agenda = {dia: DIA_ESTRUTURA.copy() for dia in DIAS_SEMANA}
    st.session_state.quadras = {dia: None for dia in DIAS_SEMANA}
    save_data(st.session_state.volei_agenda)
    save_quadras(st.session_state.quadras)

# Inicialização dos dados
def initialize_data():
    if should_reset():
        reset_week_data()
    else:
        if 'volei_agenda' not in st.session_state:
            loaded_data = load_data()
            # Garante que todos os dias estão presentes
            st.session_state.volei_agenda = {dia: loaded_data.get(dia, DIA_ESTRUTURA.copy()) for dia in DIAS_SEMANA}
            save_data(st.session_state.volei_agenda)
        
        if 'quadras' not in st.session_state:
            st.session_state.quadras = load_quadras()
            if not st.session_state.quadras:
                st.session_state.quadras = {dia: None for dia in DIAS_SEMANA}
                save_quadras(st.session_state.quadras)

# Função para remover jogador
def remove_name(day, name, role):
    day_data = st.session_state.volei_agenda[day]
    
    if name in day_data[role]:
        day_data[role].remove(name)
        
        if role == "Titulares" and day_data["Reservas"]:
            promoted = day_data["Reservas"].pop(0)
            day_data["Titulares"].append(promoted)
            if day_data["Substitutos"]:
                new_reserva = day_data["Substitutos"].pop(0)
                day_data["Reservas"].append(new_reserva)
        elif role == "Reservas" and day_data["Substitutos"]:
            promoted = day_data["Substitutos"].pop(0)
            day_data["Reservas"].append(promoted)
        
        save_data(st.session_state.volei_agenda)
        st.rerun()

# Função para remover quadra
def remove_quadra(day):
    st.session_state.quadras[day] = None
    st.session_state.volei_agenda[day]['Quadra'] = None
    save_quadras(st.session_state.quadras)
    save_data(st.session_state.volei_agenda)
    st.rerun()

# Inicializa os dados
initialize_data()

# Layout principal com abas
tab1, tab2 = st.tabs(["Início", "Listas da Semana"])

with tab1:
    st.title("VOLEIZINHO PRA CURAR ONDE DÓI 🏐🩹🌈")
    st.write("""
    **Como usar:**
    - Na aba 'Listas da Semana', selecione os dias que deseja jogar
    - Digite seu nome e clique em 'Entrar na Lista'
    - Atribua uma quadra para cada dia dentro da aba do dia
    - Para sair de uma lista, clique no ❌ ao lado do seu nome

    **Regras das listas**
    1) jogamos sempre a partir das listas criadas no grupo; 📝

    2) estabelecemos uma lista de 15 pessoas + 3 reservas para os jogos, mais a lista de substituições, por ordem de preenchimento. 
    primeiro entram para a lista os "reservas" e conforme for liberando vaga entram os "substitutos", de forma automática, no lugar de pessoas desistentes. 
    
    PORTANTO: 🔄
    
    reserva: joga revezando
    
    substituto: entra para a lista somente conforme as desistências 
    
    3) precisamos nos atentar para aqueles que colocam o nome na lista e não comparecem, já que isso prejudica aqueles que querem jogar e estão na lista de espera. lembrem de avisar com antecedência (tolerância de 2x, depois precisaremos tirar do grupo) 🔴
    
    4) jogadores de fora só podem entrar na lista caso esteja sobrando lugar NO DIA do jogo, dando prioridade aos participantes do grupo.

    5) vamos nos atentar aos horários, já que as vezes começamos a jogar 30min depois do nosso horário. claro que sempre pode acontecer por causa de trabalho e trânsito, mas precisamos manter o comprometimento com o grupo da melhor forma possível.

    ademais, vamos curar onde dói! 🩹
    """)

with tab2:
    st.title("Listas da Semana 🏐")
    
    # Seção para adicionar jogadores
    st.subheader("Adicionar Jogador")
    days_selected = st.multiselect(
        "Escolha os dias para jogar:",
        options=DIAS_SEMANA,
        key="multiselect_dias_jogar"
    )
    
    name = st.text_input("Seu nome:", key="input_nome_jogador")
    
    if st.button("Entrar na Lista", key="botao_entrar_lista") and name:
        for day in days_selected:
            day_data = st.session_state.volei_agenda[day]
            if name in day_data['Titulares'] + day_data['Reservas'] + day_data['Substitutos']:
                st.warning(f"Você já está na lista de {day}!")
            else:
                if len(day_data['Titulares']) < 15:
                    day_data['Titulares'].append(name)
                elif len(day_data['Reservas']) < 3:
                    day_data['Reservas'].append(name)
                else:
                    day_data['Substitutos'].append(name)
                st.success(f"{name} adicionado à lista de {day}!")
        
        save_data(st.session_state.volei_agenda)
        st.rerun()
    
    # Exibição das listas por dia
    tabs = st.tabs(DIAS_SEMANA)
    
    for tab, day in zip(tabs, DIAS_SEMANA):
        with tab:
            current_quadra = st.session_state.quadras.get(day)
            data = st.session_state.volei_agenda[day]
            
            # Layout com duas colunas: Listas e Quadra
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{day}**")
                
                # Listas de jogadores
                st.write(f"**Titulares ({len(data['Titulares'])}/15):**")
                for i, name in enumerate(data['Titulares']):
                    cols = st.columns([4, 1])
                    cols[0].write(f"{i+1}. {name}")
                    if cols[1].button("❌", key=f"rem_tit_{day}_{name}"):
                        st.session_state[f"show_confirm_tit_{day}_{name}"] = True
                
                # Popover de confirmação para titulares
                for i, name in enumerate(data['Titulares']):
                    if st.session_state.get(f"show_confirm_tit_{day}_{name}"):
                        with st.popover(f"Confirmar remoção de {name}"):
                            st.write(f"Tem certeza que deseja remover {name} dos titulares?")
                            if st.button("Sim", key=f"confirm_yes_tit_{day}_{name}"):
                                remove_name(day, name, 'Titulares')
                                del st.session_state[f"show_confirm_tit_{day}_{name}"]
                            if st.button("Cancelar", key=f"confirm_no_tit_{day}_{name}"):
                                del st.session_state[f"show_confirm_tit_{day}_{name}"]
                                st.rerun()
                
                st.write(f"**Reservas ({len(data['Reservas'])}/3):**")
                for i, name in enumerate(data['Reservas']):
                    cols = st.columns([4, 1])
                    cols[0].write(f"{i+1}. {name}")
                    if cols[1].button("❌", key=f"rem_res_{day}_{name}"):
                        st.session_state[f"show_confirm_res_{day}_{name}"] = True
                
                for i, name in enumerate(data['Reservas']):
                    if st.session_state.get(f"show_confirm_res_{day}_{name}"):
                        with st.popover(f"Confirmar remoção de {name}"):
                            st.write(f"Tem certeza que deseja remover {name} dos reservas?")
                            if st.button("Sim", key=f"confirm_yes_res_{day}_{name}"):
                                remove_name(day, name, 'Reservas')
                                del st.session_state[f"show_confirm_res_{day}_{name}"]
                            if st.button("Cancelar", key=f"confirm_no_res_{day}_{name}"):
                                del st.session_state[f"show_confirm_res_{day}_{name}"]
                                st.rerun()
                
                st.write("**Substitutos:**")
                for i, name in enumerate(data['Substitutos']):
                    cols = st.columns([4, 1])
                    cols[0].write(f"{i+1}. {name}")
                    if cols[1].button("❌", key=f"rem_sub_{day}_{name}"):
                        st.session_state[f"show_confirm_sub_{day}_{name}"] = True
                
                for i, name in enumerate(data['Substitutos']):
                    if st.session_state.get(f"show_confirm_sub_{day}_{name}"):
                        with st.popover(f"Confirmar remoção de {name}"):
                            st.write(f"Tem certeza que deseja remover {name} dos substitutos?")
                            if st.button("Sim", key=f"confirm_yes_sub_{day}_{name}"):
                                remove_name(day, name, 'Substitutos')
                                del st.session_state[f"show_confirm_sub_{day}_{name}"]
                            if st.button("Cancelar", key=f"confirm_no_sub_{day}_{name}"):
                                del st.session_state[f"show_confirm_sub_{day}_{name}"]
                                st.rerun()
            
            with col2:
                st.markdown("**Quadra**")
                
                if current_quadra:
                    st.write(f"Quadra selecionada: **{current_quadra}**")
                    if st.button("❌ Remover", key=f"remove_quadra_{day}"):
                        st.session_state[f"show_confirm_quadra_{day}"] = True
                    
                    if st.session_state.get(f"show_confirm_quadra_{day}"):
                        with st.popover(f"Confirmar remoção da quadra"):
                            st.write("Tem certeza que deseja remover esta quadra?")
                            if st.button("Sim", key=f"confirm_yes_quadra_{day}"):
                                remove_quadra(day)
                                del st.session_state[f"show_confirm_quadra_{day}"]
                            if st.button("Cancelar", key=f"confirm_no_quadra_{day}"):
                                del st.session_state[f"show_confirm_quadra_{day}"]
                                st.rerun()
                else:
                    quadra_selecionada = st.selectbox(
                        "Selecione a quadra:",
                        options=[""] + QUADRAS_DISPONIVEIS,
                        index=0,
                        key=f"quadra_select_{day}"
                    )
                    
                    if quadra_selecionada and st.button("Selecionar", key=f"select_quadra_{day}"):
                        st.session_state.quadras[day] = quadra_selecionada
                        st.session_state.volei_agenda[day]['Quadra'] = quadra_selecionada
                        save_quadras(st.session_state.quadras)
                        save_data(st.session_state.volei_agenda)
                        st.rerun()

    # Botão de reset manual com confirmação
    if st.button("Resetar Todas as Listas (Apenas Admin)", key="botao_reset_admin"):
        st.session_state['show_confirm_reset'] = True
    
    if st.session_state.get('show_confirm_reset'):
        with st.popover("Confirmar reset"):
            st.warning("Tem certeza que deseja resetar TODAS as listas?")
            if st.button("Sim, resetar tudo", key="confirm_reset_sim"):
                reset_week_data()
                st.session_state['show_confirm_reset'] = False
                st.rerun()
            if st.button("Cancelar", key="confirm_reset_nao"):
                st.session_state['show_confirm_reset'] = False
                st.rerun()
