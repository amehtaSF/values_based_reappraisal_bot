import streamlit as st
from openai import OpenAI
import yaml
import os
from utils import query_gpt, handle_chat

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = 'gpt-4o-2024-05-13'

with open('chat_flow.yaml') as f:
    chat_flow = yaml.safe_load(f)


with open('issue_question.md') as f:
    issue_question = f.read()

# Show title and description.
st.title("VBR Bot")
# st.write(issue_question)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"] )

# Initialize session state
if "messages" not in st.session_state:
    # Initialize first message
    st.session_state.messages = [{"role": "assistant", "content": issue_question}]

if "stage" not in st.session_state:
    st.session_state.stage = "solicit_issue"

if "issue" not in st.session_state:
    st.session_state.issue = []

if "values_questions" not in st.session_state:
    st.session_state.values_questions = None

# Display message history on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input():
# lasdkfjlasd imagine user just wrote their issue down, succeeded, stage is now verify_issue

    # Print user input and save to history
    handle_chat(st, user_input, "user")

    # Check if we need GPT response and make API call
    prompt = chat_flow[st.session_state.stage]['gpt']
    gpt_output = query_gpt(client, MODEL, 0.8, prompt, **st.session_state) if prompt else None

    asst_msg = chat_flow[st.session_state.stage]['msg']
    handle_chat(st, asst_msg, "assistant")
    
    