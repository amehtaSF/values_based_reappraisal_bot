import streamlit as st
from openai import OpenAI
import yaml
import os
from utils import query_gpt, handle_chat

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = 'gpt-4o-2024-05-13'

with open('prompts.yaml') as f:
    prompts = yaml.safe_load(f)


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

# if user_input := st.chat_input():
#     prompt = prompts[st.session_state.stage]['gpt']
    

if user_input := st.chat_input():
    if st.session_state.stage == "solicit_issue":
        st.session_state.issue = user_input
        handle_chat(st, user_input, "user")
        gpt_prompt = prompts["issue_values"].format(issue=user_input)
        values_questions = query_gpt(client, MODEL, .8, prompt=gpt_prompt, stream=False)
        handle_chat(st, values_questions, "assistant")
        st.session_state.values_questions = values_questions
        st.session_state.stage = "solicit_values"
    elif st.session_state.stage == "solicit_values":
        st.session_state.values = user_input
        handle_chat(st, user_input, "user")
        gpt_prompt = prompts["reappraisal_values"].format(issue=st.session_state.issue, values=st.session_state.values)
        reappraisal = query_gpt(client, MODEL, .8, prompt=gpt_prompt, stream=False)
        handle_chat(st, reappraisal, "assistant")
        st.session_state.stage = "offer_reappraisal"
    

# if st.session_state.stage == "solicit_issue":
#     if issue := st.chat_input(key="issue_input"):
#         # Display user message in chat message container
#         with st.chat_message("user"):
#             st.markdown(issue)
#         # Add user message to chat history
#         st.session_state.messages.append({"role": "user", "content": issue})
#         st.session_state.issue = issue
#         gpt_prompt = prompts["issue_values"].format(issue=issue)
#         values_questions = query_gpt(client, MODEL, .8, gpt_prompt)
#         st.session_state.values_questions = values_questions
#         st.session_state.stage = "solicit_values"

# if st.session_state.stage == "solicit_values":
#     # Display the values questions
#     with st.chat_message("assistant"):
#         st.markdown(values_questions)
#     # Add values questions to chat history
#     st.session_state.messages.append({"role": "assistant", "content": values_questions})
#     if values_response := st.chat_input(key="values_input"):
#         # Display user message in chat message container
#         with st.chat_message("user"):
#             st.markdown(values_response)
#         # Add user message to chat history
#         values = st.session_state.values_questions + values_response
#         st.session_state.messages.append({"role": "user", "content": values})
#         st.session_state.values = values
#         gpt_prompt = prompts["reappraisal"].format(issue=st.session_state.issue, values=values)
#         reappraisal = query_gpt(client, MODEL, .8, gpt_prompt)
#         st.session_state.stage = "offer_reappraisal"

# if st.session_state.stage == "offer_reappraisal":
#     # Display the reappraisal
#     with st.chat_message("assistant"):
#         st.markdown(reappraisal)
#     # Add reappraisal to chat history
#     st.session_state.messages.append({"role": "assistant", "content": reappraisal})