import streamlit as st
from streamlit import session_state as state
from openai import OpenAI
import yaml
import os
from utils import query_gpt, handle_chat
from chat import ChatStep, SolicitIssue, VerifyIssue

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
if "messages" not in state:
    # Initialize first message
    state.messages = [{"role": "assistant", "content": issue_question}]

if "stage" not in state:
    state.stage = "solicit_issue"

if "substage" not in state:
    # 0 when you are creating the question
    # 1 when you are handling the response
    # starts at 1 because the first message is already displayed
    state.substage = 1

if "issue" not in state:
    state.issue = []

if "values_questions" not in state:
    state.values_questions = None

# Display message history on screen
for message in state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input():

    if state.stage == "solicit_issue":
        step = SolicitIssue(st=st)
        step.process_user_msg(user_input)
        state.stage, state.substage = step.next_step()
        # need to run the next step here


    if state.stage == "verify_issue":
        if state.substage == 0:
            step = VerifyIssue(st=st)
            asst_msg = step.create_asst_msg()
            handle_chat(st, asst_msg, "assistant")
            state.substage = 1

        elif state.substage == 1:
            step = VerifyIssue(st=st)
            step.process_user_msg(user_input)
            state.stage = step.next_step()
            state.substage = 0

        


    if state.stage == "solicit_values":
        pass

    if state.stage == "offer_reappraisal":
        pass