import streamlit as st
from streamlit import session_state as state
from openai import OpenAI
import yaml
import os
from utils import handle_chat
import json
from chat_steps_3_reviseReap import SolicitIssue, VerifyIssue, SolicitValues, OfferReappraisal




OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = 'gpt-4o-2024-05-13'

with open('chat_flow_3_reviseReap.yaml') as f:
    chat_flow = yaml.safe_load(f)

with open('issue_question.md') as f:
    issue_question = f.read()

st.title("VBR Bot")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

chat_steps = {"solicit_issue": SolicitIssue,  
              "offer_reappraisal": OfferReappraisal}

# Initialize session state
init_state = {"messages": [{"role": "assistant", "content": issue_question}], 
              "listener": "solicit_issue", 
              "speaker": "solicit_issue", 
              "issue": [], 
            #   "issue_summary": None, 
            #   "values_question_num": 0, 
            #   "user_values": [],
              "selected_value": None,
            #   "reap_development_msgs": [],
              }

for key, value in init_state.items():
    if key not in state:
        state[key] = value

with open('value_list.json', 'r') as f:
    value_json = json.load(f)

options = [{"value": "general reappraisal",
            "description": ""}]
options = options + value_json

# Extract values and descriptions
values = [item['value'] for item in options]
value_descriptions = {item['value']: item['description'] for item in options}

# Create sidebar elements
selected_value = st.sidebar.selectbox(
    "Select an value to incorporate in the reappraisal:",
    values
)
reappraise_btn = st.sidebar.button("Reappraise", on_click=OfferReappraisal(st=st).run_speaker)

# Display the selected option's description
st.sidebar.write(f"{value_descriptions[selected_value]}")
state.selected_value = selected_value


# Display message history on screen
for message in state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input():

    # Listener step
    step = chat_steps[state.listener](st=st, user_input=user_input)
    step.run_listener()

    # Speaker step
    step = chat_steps[state.speaker](st=st, user_input=user_input)
    step.run_speaker()


