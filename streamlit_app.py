import datetime
import random
import io
import os
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from openai import OpenAI

from streamlit_oauth import OAuth2Component
from streamlit_cookies_controller import CookieController

import login_google

controller = CookieController()

DISABLE_LOGIN = False
st.session_state['DISABLE_LOGIN'] = DISABLE_LOGIN

# Show app title and description.
st.set_page_config( page_title="CTC-Tech, Descomplica Geral - RH",
                    layout="wide",
                    initial_sidebar_state="auto",
                    page_icon="🎫")

def logar_atividade(message):
    log_message = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
    st.success(log_message)

def vector_store_update(df_envio, oai_client, vec_id, file_name):
    list_vector_store_files = oai_client.beta.vector_stores.files.list(
        vector_store_id=vec_id
    )
    logar_atividade(f"Quantidade de arquivos no vector {len(list_vector_store_files.data)}")

    for vector_store_file in list_vector_store_files.data:
        deleted_vector_store_file = oai_client.beta.vector_stores.files.delete(
            vector_store_id=vec_id,
            file_id=vector_store_file.id
        )
        if deleted_vector_store_file.deleted:
            logar_atividade(f"Arquivo removido do vector com sucesso! (id = {vector_store_file.id})")
        else:
            logar_atividade(f"Não foi possível remover o arquivo do vector! (id = {vector_store_file.id})")
            return False
    
    list_files = client.files.list()
    logar_atividade(f"Quantidade de arquivos soltos sem associação! {len(list_files.data)}")

    for arquivo in list_files.data:
        logar_atividade(f"Arquivo a ser deletado! (id = {arquivo.id})" )

        file_deleted = client.files.delete(
            file_id=arquivo.id
        )

        logar_atividade(f"Arquivo deletado com sucesso! (id={file_deleted.id})")

    json_buffer = io.BytesIO()
    df_envio.to_json(json_buffer, orient='records')
    json_buffer.seek(0)
    json_buffer.name = file_name

    arquivo = oai_client.files.create(file=json_buffer, purpose='assistants')
    logar_atividade(f"Arquivo novo criado com sucesso! (id={arquivo.id})")

    create_vector_store_file = oai_client.beta.vector_stores.files.create(
        vector_store_id=vec_id,
        file_id = arquivo.id
    )

    if create_vector_store_file.last_error is None:
        logar_atividade(f"Arquivo associado ao vector com sucesso! {create_vector_store_file.id}")
    else:
        logar_atividade(f"Erro ao associar o arquivo no vector! {create_vector_store_file.last_error}")
        return False

    return True

with st.sidebar:
    st.session_state["login"] = login_google.login(controller)

if 'login' in st.session_state:
    if ( st.session_state['login'] and ( "auth" in st.session_state ) ) or st.session_state.DISABLE_LOGIN:

        #st.title("https://ctctech.com.br/")

        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1 style="text-align: center; flex-grow: 1;">Descomplica Geral - RH</h1>
                <img src="https://ctctech.com.br/wp-content/uploads/2024/04/Logo-CTC-30-branco.webp" alt="Logo" style="height: 50px;">
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("""
            Essa aplicação utiliza a AI generativa
            para responder perguntas gerais do dia-a-dia
            dos colaboradores da empresa CTC Tech."""
        )

        client = OpenAI(api_key=st.secrets.store_api_key.OPENAI_API_KEY)

        VECTOR_ID_CTC_DESCOMPLICA_GERAL = st.secrets.store_api_key.VECTOR_ID_CTC_DESCOMPLICA_GERAL
        ASSISTANT_ID_CTC_DESCOMPLICA_GERAL = st.secrets.store_api_key.ASSISTANT_ID_CTC_DESCOMPLICA_GERAL
        json_descomplica_geral = "DESCOMPLICA_GERAL.json"

        with st.spinner("Carregando..."):
            if os.path.exists(json_descomplica_geral):
                df = pd.read_json(json_descomplica_geral, orient='records', lines=True)
            else:
                data = [
                    {
                        "ID": 1,
                        "pergunta": "Qual o dia do pagamento?",
                        "resposta": "Até o dia 10 de cada mês, caso dia 10 for um feriado! será no próximo dia útil.",
                        "data": "2023-12-08",
                        "resposavel": "RH"
                    },
                    {
                        "ID": 2,
                        "pergunta": "Qual o dia do aniversário da empresa CTC?",
                        "resposta": "O aniversário da empresa é 1 de janeiro.",
                        "data": "2023-12-08",
                        "resposavel": "Diretoria"
                    },
                ]

                df = pd.DataFrame( data )

                # Conversão da coluna 'data' para o tipo datetime
                df['data'] = pd.to_datetime(df['data'], errors='coerce')

                # Verificação de valores não convertidos
                if df['data'].isnull().any():
                    print("Algumas datas não foram convertidas corretamente.")

                # Formatação da coluna 'data' para o formato 'DD/MM/YYYY'
                df['data'] = df['data'].dt.strftime('%d/%m/%Y')

                df.to_json(json_descomplica_geral, orient='records', lines=True)

        # Show a section to add a new faq.
        st.header("Adicione uma nova pergunta aos conhecimentos gerais da CTC.")

        # We're adding faqs via an `st.form` and some input widgets. If widgets are used
        # in a form, the app will only rerun once the submit button is pressed.
        with st.form("add_faq_form"):
            pergunta   = st.text_input(label="Descreva a pergunta")
            resposta   = st.text_area(label="Descreva a resposta")
            data       = st.date_input(label="Data", value=datetime.datetime.now())
            resposavel = st.selectbox("Resposável pela informação", ["RH", "Comercial", "Diretoria", "Outros"])
            submitted  = st.form_submit_button("Salvar")

        log_area = st.empty()  # Espaço reservado para o log

        if submitted:
            recent_faq_number = int(max(df.ID))
            df_new = pd.DataFrame(
                [
                    {
                        "ID" : recent_faq_number+1,
                        "pergunta": pergunta,
                        "resposta": resposta,
                        "data": datetime.datetime.now(),
                        "resposavel" : resposavel
                    }
                ]
            )

            df = pd.concat([df_new, df], axis=0)
            df.to_json(json_descomplica_geral, orient='records', lines=True)
            st.success("Salvo com sucesso! verifique a tabela abaixo:")

            result = vector_store_update(df, client, VECTOR_ID_CTC_DESCOMPLICA_GERAL, json_descomplica_geral)
            st.success('AI atualizada com sucesso!')

        st.header("Perguntas existentes")
        st.write(f"Número de perguntas: `{len(df)}`")

        st.info(
            "Para editar você pode dar um duplo click na linha! "
            "Após editar click em 'Salvar edições'",
            icon="✍️",
        )

        # Supondo que df seja o seu DataFrame
        df['data'] = pd.to_datetime(df['data'], errors='coerce')

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "pergunta": st.column_config.TextColumn(
                    label="Pergunta",
                    help="Pergunta"
                ),
                "resposta": st.column_config.TextColumn(
                    label="Resposta",
                    help="Resposta"
                ),
                "resposavel": st.column_config.SelectboxColumn(
                    label="Resposável",
                    help="Resposável",
                    options=["RH", "Comercial", "Diretoria", "Outros"],
                ),
                "data": st.column_config.DateColumn(
                    label="Data",
                    #min_value=date(2024, 1, 1),
                    #max_value=date(2025, 12, 31),
                    format='DD/MM/YYYY'
                )
            },

            disabled=["ID"],
        )

        # Botão para salvar as edições
        if st.button('Salvar edições'):
            edited_df.to_json(json_descomplica_geral, orient='records', lines=True)
            st.success('Edições salvas com sucesso!')

            result = vector_store_update(edited_df, client, VECTOR_ID_CTC_DESCOMPLICA_GERAL, json_descomplica_geral)
            st.success('AI atualizada com sucesso!')

        st.header("Estatisticas")

        col1, col2, col3, col4, col5 = st.columns(5)
        num_open_faqs = len(df)
        col1.metric(label="Numero de Perguntas", value=num_open_faqs, delta=1)
        col2.metric(label="RH",                  value=len(df[df.resposavel == "RH"]), delta=1)
        col3.metric(label="Comercial",           value=len(df[df.resposavel == "Comercial"]), delta=-0)
        col4.metric(label="Diretoria",           value=len(df[df.resposavel == "Diretoria"]), delta=-0)
        col5.metric(label="Outros",              value=len(df[df.resposavel == "Outros"]), delta=-0)