import streamlit as st
import json
import math
import base64
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="KO Drum Rating App", layout="wide")

# --- Session State Initialization ---
INPUT_KEYS = ['tag_no', 'rev_no', 'service', 'project', 'date_str', 
              'W_V', 'rho_V', 'mu_V', 'W_L', 'rho_L', 'D', 'H', 'D_p_um', 'user_conclusion']

for key in INPUT_KEYS:
    if key not in st.session_state:
        if key == 'project': st.session_state[key] = "SK Trichem Project"
        elif key == 'date_str': st.session_state[key] = datetime.now().strftime("%Y-%m-%d")
        elif key == 'tag_no': st.session_state[key] = "V-101"
        elif key == 'rev_no': st.session_state[key] = "0"
        elif key == 'service': st.session_state[key] = "Flare KO Drum"
        elif key == 'W_V': st.session_state[key] = 2239.8
        elif key == 'rho_V': st.session_state[key] = 5.679
        elif key == 'mu_V': st.session_state[key] = 0.000009
        elif key == 'W_L': st.session_state[key] = 25360.4
        elif key == 'rho_L': st.session_state[key] = 824.5
        elif key == 'D': st.session_state[key] = 0.6
        elif key == 'H': st.session_state[key] = 1.53
        elif key == 'D_p_um': st.session_state[key] = 300.0
        elif key == 'user_conclusion': st.session_state[key] = ""

# --- Sidebar: Secure JSON Data Loader ---
st.sidebar.header("💾 Secure JSON Data Loader")
json_input = st.sidebar.text_area("JSON Input Text", height=150)
if st.sidebar.button("Load JSON Data"):
    if json_input.strip():
        try:
            data = json.loads(json_input)
            for k, v in data.items():
                if k in st.session_state:
                    st.session_state[k] = v
            st.sidebar.success("✅ Data applied! Please refresh.")
        except json.JSONDecodeError:
            st.sidebar.error("❌ Invalid JSON format.")

data_to_save = {key: st.session_state[key] for key in INPUT_KEYS}
st.sidebar.text_area("Copy
