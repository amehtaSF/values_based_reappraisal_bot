import yaml
from openai import OpenAI
import json 
from pprint import pprint

with open('chat_flow_4_emotions.yaml') as f:
    chat_flow = yaml.safe_load(f)

with open('value_list.json', 'r') as f:
    value_json = json.load(f)

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
        
        self.COMMANDS = ["REAPPRAISE"]

    def add_message(self, role, content):
        '''Add a message to the message history in the session state.'''
        self.st.session_state.messages.append({"role": role, "content": content})

    def chat_msg(self, role, content):
        # if content in self.COMMANDS:
        #     return
        self.add_message(role, content)
        with self.st.chat_message(role):
            self.st.markdown(content)


class SolicitIssue(ChatStep):

    def __init__(self, st, user_input):
        super().__init__(st, user_input)
        self.name = "solicit_issue"


    def get_next_question(self):
        '''Gets the next question to ask the user'''
        msgs = self.st.session_state.issue + [{"role": "system", "content": chat_flow[self.name]["speaker"]["gpt"]}]
        gpt_response = client.chat.completions.create(
            model=MODEL,
            temperature=chat_flow[self.name]["speaker"]["temperature"],
            messages=msgs)
        next_question = gpt_response.choices[0].message.content
        return next_question

    def next_step(self):    
        self.st.session_state.listener = "solicit_emotions"
        self.st.session_state.speaker = "solicit_emotions"

    def run_listener(self):
        self.chat_msg("user", self.user_input)
        self.st.session_state.issue.append({"role": "user", "content": self.user_input})
        self.next_step()

    def run_speaker(self):
        msg = self.get_next_question()
        self.chat_msg("assistant", msg)
        self.st.session_state.issue.append({"role": "assistant", "content": msg})
        

class OfferReappraisal(ChatStep):

    '''
    Speaker: Offers a reappraisal of the issue.
    '''

    def __init__(self, st, user_input=None):
        super().__init__(st, user_input)
        self.name = "offer_reappraisal"

    def gpt_reappraise(self, value_option=None):
        '''sends issue and values to GPT and asks for a reappraisal without revising step'''
    
        if not value_option or value_option not in [item['value'] for item in value_json]:
            # get the general reappraisal prompt
            prompt = chat_flow[self.name]["speaker"]["gpt_general_reappraisal"]
        else:
            # get a value based reappraisal prompt
            prompt_template = chat_flow[self.name]["speaker"]["gpt_value_reappraisal"]
            description = [item['description'] for item in value_json if item['value'] == value_option][0]
            prompt = prompt_template.format(value=value_option, description=description)

        # solicit a reappraisal from gpt
        emo_msgs = [{"role": "user", "content": f"<emotion>{emo}</emotion> <reason>{reason}</reason>"} for emo, reason in self.st.session_state.emotions.items() if reason is not None]
        gpt_msg = {"role": "system", "content": prompt}
        gpt_output = client.chat.completions.create(
            model=MODEL,
            temperature=chat_flow[self.name]["speaker"]["temperature"],
            messages=self.st.session_state.issue + emo_msgs + [gpt_msg])
        gpt_output_reap = gpt_output.choices[0].message.content

        return gpt_output_reap
    
    def create_asst_msg(self):
        asst_msg = self.gpt_reappraise(self.st.session_state.selected_value)
        return asst_msg

    def run_speaker(self):
        asst_msg = self.create_asst_msg()
        self.chat_msg("assistant", asst_msg)

    def run_listener(self):
        self.chat_msg("user", self.user_input)
        

class SolicitEmotions(ChatStep):

    def __init__(self, st, user_input):
        super().__init__(st, user_input)
        self.name = "solicit_emotions"
        

    def update_emotions(self, **kwargs):
        emos = self.st.session_state.selected_emotions
        for emo in emos:
            if emo not in self.st.session_state.emotions:
                self.st.session_state.emotions[emo] = None
            if emo in kwargs.keys():
                self.st.session_state.emotions[emo] = kwargs[emo]
        # remove anything from self.st.session_state.emotions that is not in emos
        for emo in self.st.session_state.emotions:
            if emo not in emos:
                del self.st.session_state.emotions[emo]

    def next_step(self):
        # check if any values in the emotions dict are None
        if None in self.st.session_state.emotions.values():
            self.st.session_state.listener = "solicit_emotions"
            self.st.session_state.speaker = "solicit_emotions"
        else:
            self.st.session_state.listener = "offer_reappraisal"
            self.st.session_state.speaker = "offer_reappraisal"
    
    def get_unexplained_emo(self):
        emos = self.st.session_state.emotions
        for emo, val in emos.items():
            if val is None:
                return emo
        return None

    def run_listener(self):
        self.chat_msg("user", self.user_input)
        kw = {self.st.session_state.discussing_emotion: self.user_input}
        self.update_emotions(**kw)
        self.next_step()

    def run_speaker(self):
        emo = self.get_unexplained_emo()
        self.st.session_state.discussing_emotion = emo
        msg = chat_flow[self.name]["speaker"]["chat_msg"].format(emotion=emo)
        self.chat_msg("assistant", msg)

        

