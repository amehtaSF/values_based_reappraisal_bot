import yaml
from openai import OpenAI

with open('chat_flow_5.yaml') as f:
    chat_flow = yaml.safe_load(f)

MODEL = 'gpt-4o-2024-05-13'

client = OpenAI()

'''
For any given step in the chat flow, we need to:
LISTENER
- Process the user's message
- Determine the next step in the chat flow, i.e. choose a speaker step
SPEAKER
- Process whatever is needed to formulate next chat message
- Send a message to the user

The first two steps are done by one class and the second two steps are done by another class.
When we are processing the user message and identifying the next step, we can call that the "listener" step.
When we are processing the next chat message and sending it to the user, we can call that the "speaker" step.

The listener uses methods to listen to the response from the message that was sent by the speaker of the same class.

'''

class ChatStep:

    def __init__(self, st, user_input):
        
        self.st = st
        self.user_input = user_input
        self.name = None

    def add_message(self, role, content):
        '''Add a message to the message history in the session state.'''
        self.st.session_state.messages.append({"role": role, "content": content})

    def chat_msg(self, role, content):
        self.add_message(role, content)
        with self.st.chat_message(role):
            self.st.markdown(content)



class SolicitIssue(ChatStep):

    '''
    Listener: Saves the user's issue to the session state and moves to verify_issue.
    Speaker: (There is no speaker step for this class because this is where the bot starts.)
    '''
    
    def __init__(self, st, user_input):
        super().__init__(st, user_input)
        self.name = "solicit_issue"

    def create_asst_msg(self):
        asst_msg = chat_flow[self.name]["asst_msg"]
        return asst_msg

    def save_user_msg(self, user_input):
        self.chat_msg("user", user_input)
        self.st.session_state.issue.append({"role": "user", "content": user_input})
        self.st.session_state.messages.append({"role": "user", "content": user_input})
        
    def next_step(self):
        next_listener = "verify_issue"
        next_speaker = "verify_issue"
        self.st.session_state.listener = next_listener
        self.st.session_state.speaker = next_speaker
        return next_listener, next_speaker
    
    def run_listener(self):
        self.save_user_msg(self.user_input)
        self.next_step()


class VerifyIssue(ChatStep):

    '''Makes a summary of the main points of the issue and asks the user to verify.
    Loops until the user confirms the issue summary is good.'''

    def __init__(self, st, user_input):
        super().__init__(st, user_input)
        self.name = "verify_issue"

    def process_inputs(self):
        '''sends all issue related messages to gpt and asks it to summarize the issue'''
        gpt_msg = {"role": "system", "content": chat_flow[self.name]["listener"]["gpt"]}
        messages = self.st.session_state.issue + [gpt_msg]
        gpt_response = client.chat.completions.create(
            model=MODEL,
            temperature=chat_flow[self.name]["listener"]["temperature"],
            messages=messages)
        gpt_output = gpt_response.choices[0].message.content
        self.st.session_state.issue_summary = gpt_output
        return gpt_output
    
    def create_asst_msg(self):
        asst_msg = chat_flow[self.name]["speaker"]["asst_msg"].format(gpt_output=self.process_inputs())
        self.st.session_state.issue.append({"role": "assistant", "content": asst_msg})
        return asst_msg
    
    def save_user_msg(self, user_input):
        self.chat_msg("user", user_input)
        self.st.session_state.issue.append({"role": "user", "content": user_input})
    
    def next_step(self):
        gpt_msg = {"role": "system", "content": chat_flow[self.name]["speaker"]["gpt"]}
        messages = self.st.session_state.issue + [gpt_msg]
        gpt_response = client.chat.completions.create(
            model=MODEL,
            temperature=chat_flow[self.name]["speaker"]["temperature"],
            messages=messages)
        gpt_output = int(gpt_response.choices[0].message.content)
        assert gpt_output in [1, 0]
        if gpt_output == 1:
            self.st.session_state.listener = "solicit_values"
            self.st.session_state.speaker = "solicit_values"
        elif gpt_output == 0:
            self.st.session_state.listener = "verify_issue"
            self.st.session_state.speaker = "verify_issue"
        else:
            raise ValueError("GPT output was not 1 or 0.")
    
    def run_listener(self):
        self.save_user_msg(self.user_input)
        self.next_step()
    
    def run_speaker(self):
        asst_msg = self.create_asst_msg()
        self.chat_msg("assistant", asst_msg)


        
class SolicitValues(ChatStep):

    '''
    Speaker: Asks the user to provide values related to the issue.
    Listener: Saves the user's values to the session state and moves to offer_reappraisal.
    '''

    def __init__(self, st, user_input):
        super().__init__(st, user_input)
        self.name = "solicit_values"
    
    def gpt_summarize_issue(self):
        '''sends all issue related messages to gpt and asks it to summarize the issue'''
        gpt_msg = {"role": "system", "content": chat_flow[self.name]["speaker"]["gpt"]}
        messages = self.st.session_state.issue + [gpt_msg]
        gpt_response = client.chat.completions.create(
            model=MODEL,
            temperature=chat_flow[self.name]["speaker"]["temperature"],
            messages=messages)
        gpt_output = gpt_response.choices[0].message.content
        self.st.session_state.values_questions = gpt_output
        return gpt_output
    
    def create_asst_msg(self):
        asst_msg = self.gpt_summarize_issue()
        return asst_msg

    def save_user_msg(self, user_input):
        self.chat_msg("user", user_input)
        self.st.session_state.user_values.append({"role": "user", "content": user_input})

    def next_step(self):
        self.st.session_state.listener = "offer_reappraisal"
        self.st.session_state.speaker = "offer_reappraisal"

    def run_listener(self):
        self.save_user_msg(self.user_input)
        self.next_step()     

    def run_speaker(self):
        asst_msg = self.create_asst_msg()
        self.chat_msg("assistant", asst_msg)
        

class OfferReappraisal(ChatStep):

    '''
    Speaker: Offers a reappraisal of the issue.

    '''

    def __init__(self, st, user_input):
        super().__init__(st, user_input)
        self.name = "offer_reappraisal"

    def gpt_reappraise(self):
        '''sends issue and values to GPT and asks for a reappraisal'''
        gpt_content = chat_flow[self.name]["speaker"]["gpt"].format(user_values=self.st.session_state.user_values)
        gpt_msg = {"role": "system", "content": gpt_content}
        gpt_output = client.chat.completions.create(
            model=MODEL,
            temperature=chat_flow[self.name]["speaker"]["temperature"],
            messages=self.st.session_state.issue + [gpt_msg])
        return gpt_output.choices[0].message.content
    
    def create_asst_msg(self):
        asst_msg = self.gpt_reappraise()
        return asst_msg
    
    def run_speaker(self):
        asst_msg = self.create_asst_msg()
        self.chat_msg("assistant", asst_msg)

