import streamlit as st
from streamlit_oauth import OAuth2Component

from streamlit_cookies_controller import CookieController

import logging
logging.basicConfig(level=logging.INFO)

import os, time
import base64
import json

# create an OAuth2Component instance
CLIENT_ID = st.secrets.store_api_key.GCLIENT_ID
CLIENT_SECRET = st.secrets.store_api_key.GCLIENT_SECRET
AUTHORIZE_ENDPOINT = st.secrets.store_api_key.GAUTHORIZE_ENDPOINT
TOKEN_ENDPOINT = st.secrets.store_api_key.GTOKEN_ENDPOINT
REVOKE_ENDPOINT = st.secrets.store_api_key.GREVOKE_ENDPOINT
REDIRECT_URIS = st.secrets.store_api_key.GREDIRECT_URIS
PREAUTHORIZED_EMAILS = st.secrets.preauthorized_emails.emails

def logout(controller):
    if 'auth' in st.session_state:
        del st.session_state["auth"]
        controller.remove('cookie_auth')

    if 'token' in st.session_state:
        del st.session_state["token"]
        controller.remove('cookie_token')

def login(controller):
    #cookies = controller.getAll()
    #st.write(cookies)

    cookie_auth = controller.get('cookie_auth')
    if cookie_auth:
        #st.write(cookie_auth)
        logging.info(cookie_auth)
        st.session_state["auth"] = cookie_auth

    cookie_token = controller.get('cookie_token' )
    if cookie_token:
        #st.write(cookie_token)
        logging.info(cookie_token)
        st.session_state["token"] = cookie_token

    if "auth" not in st.session_state:
        # create a button to start the OAuth2 flow
        oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, TOKEN_ENDPOINT, REVOKE_ENDPOINT)

        result = oauth2.authorize_button(
            name="Faça login com sua conta Google",
            icon="https://www.google.com/favicon.ico",
            redirect_uri=REDIRECT_URIS,
            scope="openid email profile",
            key="google",
            extras_params={"prompt": "consent", "access_type": "offline"},
            use_container_width=False 
        )

        if result:
            id_token = result["token"]["id_token"]
            payload = id_token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            payload = json.loads(base64.b64decode(payload))
            email = payload["email"]

            st.session_state["auth"] = email
            controller.set('cookie_auth', email )

            st.session_state["token"] = result["token"]
            controller.set('cookie_token', result["token"] )

            time.sleep(0.5)
            st.rerun()
    else:
        st.write("Você está logado!")
        st.write('Seu email é :', st.session_state["auth"])

        if st.button("Logout"):
            logout(controller)

        if st.session_state['auth'] in PREAUTHORIZED_EMAILS:
            return True, st.session_state["auth"]
        
    st.write("Você não está logado!")
    return False, 'Acesso restrito.'