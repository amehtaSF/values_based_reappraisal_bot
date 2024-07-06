

def query_gpt(client, model, temperature, prompt, **kwargs) -> str:
    completion = client.chat.completions.create(
    model=model,
    temperature=temperature,
    messages=[
        {"role": "system", 
        "content": prompt.format(**kwargs)}
         ])
    return str(completion.choices[0].message.content)