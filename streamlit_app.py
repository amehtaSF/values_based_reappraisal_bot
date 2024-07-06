import streamlit as st
from openai import OpenAI
import yaml
import os
from utils import query_gpt

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = 'gpt-4o-2024-05-13'

with open('prompts.yaml') as f:
    prompts = yaml.safe_load(f)


with open('issue_question.md') as f:
    issue_question = f.read()

# Show title and description.
st.title("VBR Bot")
st.write(issue_question)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"] )

# Create a session state variable to store the chat messages. This ensures that the
# messages persist across reruns.
if "messages" not in st.session_state:
    st.session_state.messages = []

if "issue" not in st.session_state:
    st.session_state.issue = None

if "issue_values" not in st.session_state:
    st.session_state.values = None

if "reappraisal" not in st.session_state:
    st.session_state.reappraisal = None

if "stage" not in st.session_state:
    # stages: solicit_issue, solicit_values, offer_reappraisal
    st.session_state.stage = "solicit_issue"

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ------ Solicit the issue from the user. ------ #
if st.session_state.stage == "solicit_issue":
    gpt_prompt = prompts["issue_values"]
    if issue := st.text_area(issue_question, key="issue"):
        st.session_state.issue = issue
        st.session_state.stage = "solicit_values"
        gpt_prompt = gpt_prompt.format(issue=issue)
        st.session_state.values = query_gpt(client, MODEL, .8, gpt_prompt)
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.values})

        # print the values
        with st.chat_message("assistant"):
            st.markdown(st.session_state.values)
    



# --- delete all below --- #

# Create a chat input field to allow the user to enter a message. This will display
# automatically at the bottom of the page.
if issue := st.chat_input(issue_question):

    # Store and display the current prompt.
    st.session_state.messages.append({"role": "user", "content": issue})
    with st.chat_message("user"):
        st.markdown(issue)

    # Generate a response using the OpenAI API.
    stream = client.chat.completions.create(
        model=MODEL,
        temperature=.8,
        messages=[
            {"role": "system", 
             "content": prompts["issue_values"].format(issue=issue)}
        ],
        stream=True
    )


    # Stream the response to the chat using `st.write_stream`, then store it in 
    # session state.
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
