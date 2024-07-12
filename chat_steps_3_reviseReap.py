import yaml
from openai import OpenAI
import json 
from pprint import pprint

with open('chat_flow_3_reviseReap.yaml') as f:
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
        # check if the user message is "REAPPRAISE" and if so go to the reappraisal step
        if self.user_input.upper() == "REAPPRAISE":
            # remove the last item from the issue list
            _ = self.st.session_state.issue.pop()
            # remove the last message 
            _ = self.st.session_state.messages.pop()

            self.st.session_state.listener = "offer_reappraisal"
            self.st.session_state.speaker = "offer_reappraisal"
        else:
            self.st.session_state.listener = "solicit_issue"
            self.st.session_state.speaker = "solicit_issue"

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
            prompt = chat_flow[self.name]["speaker"]["gpt_general_reappraisal"]
        else:
            prompt_template = chat_flow[self.name]["speaker"]["gpt_value_reappraisal"]
            description = [item['description'] for item in value_json if item['value'] == value_option][0]
            prompt = prompt_template.format(value=value_option, description=description)

        # solicit a reappraisal from gpt
        gpt_msg = {"role": "system", "content": prompt}
        gpt_output = client.chat.completions.create(
            model=MODEL,
            temperature=chat_flow[self.name]["speaker"]["temperature"],
            messages=self.st.session_state.issue + [gpt_msg])
        gpt_output_reap = gpt_output.choices[0].message.content

        return gpt_output_reap
        

    # def gpt_reappraise(self, value_option=None):
    #     '''sends issue and values to GPT and asks for a reappraisal, then revises reappraisal'''
    #     if not value_option:
    #         value_option = "general reappraisal"
    #     value_option_edit = value_option.lower().replace(" ", "_").replace("-", "_")
    #     print(f"Value option edit: {value_option_edit}")
    #     prompt_key = "gpt_" + value_option_edit

    #     if prompt_key not in chat_flow[self.name]["speaker"]:
    #         prompt_key = "gpt_general_reappraisal"

    #     # solicit a reappraisal from gpt
    #     gpt_content = chat_flow[self.name]["speaker"][prompt_key]
    #     gpt_msg = {"role": "system", "content": gpt_content}
    #     gpt_output = client.chat.completions.create(
    #         model=MODEL,
    #         temperature=chat_flow[self.name]["speaker"]["temperature"],
    #         messages=self.st.session_state.issue + [gpt_msg])
    #     gpt_output_reap_1 = gpt_output.choices[0].message.content
    #     if prompt_key == "gpt_general_reappraisal":
    #         # if it is not value based, return the message without improving it
    #         return gpt_output_reap_1
        
    #     # save the issue and reappraisal to the session state to build a sequence upon which to improve
    #     # self.st.session_state.reap_development_msgs.append(self.st.session_state.issue)
    #     reap_development_msgs = self.st.session_state.issue
    #     reap_development_msgs.append({"role": "assistant", "content": gpt_output_reap_1})    
        
    #     # find strengths and weaknesses
    #     gpt_strength_weakness_prompt = chat_flow[self.name]["speaker"]["gpt_strength_weakness"]
    #     value_description = [item['description'] for item in value_json if item['value'] == value_option][0]
    #     gpt_msg = {"role": "system", "content": gpt_strength_weakness_prompt.format(value=value_option, description=value_description)}
    #     reap_development_msgs.append(gpt_msg)
    #     # print(reap_development_msgs)
    #     gpt_output = client.chat.completions.create(
    #         model=MODEL,
    #         temperature=chat_flow[self.name]["speaker"]["temperature"],
    #         messages=reap_development_msgs)
    #     gpt_output_judge_reap = gpt_output.choices[0].message.content
    #     reap_development_msgs.append({"role": "assistant", "content": gpt_output_judge_reap})

    #     # revise reap
    #     gpt_msg = {"role": "system", "content": chat_flow[self.name]["speaker"]["gpt_new_reap"]}
    #     reap_development_msgs.append(gpt_msg)
    #     gpt_output = client.chat.completions.create(
    #         model=MODEL,
    #         temperature=chat_flow[self.name]["speaker"]["temperature"],
    #         messages=reap_development_msgs)
    #     gpt_output_reap_2 = gpt_output.choices[0].message.content
    #     reap_development_msgs.append({"role": "assistant", "content": gpt_output_reap_2})

    #     # pprint(reap_development_msgs)
    #     # return gpt_output_reap_2
    #     chat_out = f""" {gpt_output_reap_1}

    #     {gpt_output_reap_2}
    #     ```{json.dumps(reap_development_msgs, indent=2)}```"""
    #     return chat_out
        


    
    def create_asst_msg(self):
        asst_msg = self.gpt_reappraise(self.st.session_state.selected_value)
        return asst_msg
    
    # def next_step(self):
    #     if self.user_input.upper() == "ISSUE":
            
    #         # remove the last message 
    #         _ = self.st.session_state.messages.pop()

    #         self.st.session_state.listener = "solicit_issue"
    #         self.st.session_state.speaker = "solicit_issue"
    #     else:
    #         self.st.session_state.listener = "offer_reappraisal"
    #         self.st.session_state.speaker = "offer_reappraisal"
    
    def run_speaker(self):
        asst_msg = self.create_asst_msg()
        self.chat_msg("assistant", asst_msg)

    def run_listener(self):
        self.chat_msg("user", self.user_input)



class AssessIssueCompleteness:

    pass
