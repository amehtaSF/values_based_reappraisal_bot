

def query_gpt(client, model, temperature, prompt=None, messages=None, stream=False, **kwargs) -> str:
    assert prompt or messages, "Prompt or messages must be provided"
    messages = [{"role": "system", "content": prompt.format(**kwargs)}] if not messages else messages
    completion = client.chat.completions.create(
    model=model,
    temperature=temperature,
    messages=messages
    ),
    try: 
        return str(completion[0].choices[0].message.content)
    except Exception as e:
        return "Error with GPT API call"
    
def handle_chat(st, content, role):
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)