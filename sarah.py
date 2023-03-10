import requests
import IPython

import openai

PROMPT = """
You are a coding assistant integrated into interactive ipython shell. You take
requests from the user in natural language and produce code snippets that the
user can execute right away in their ipython session.

* Make sure all code snippets are surrounded with '```'. You may output multiple code snippets. User will select at most one to execute

* You can assume user executed all previously generated snippets

* Make the snippets short, if possible one line. Avoid comments and print statements
"""

class MetaAsk(type):
    @property
    def ac(cls):
        cls.ask_cont()
    @property
    def a(cls):
        cls.ask()

class ask(object, metaclass=MetaAsk):

    @classmethod
    def ask(cls):
        cls.current_session = None
        cls.ask_cont()


    @classmethod
    def ask_cont(cls):
        session = cls.get_current_session()
        text = input('> ')
        session.append({"role": "user", "content": text})
        for trial in range(3):
            completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", 
                    messages=session
                )

            message = completion['choices'][0]['message']
            session.append(message)
            cls.current_session = session
            snippets = message['content'].split('```')[1::2]
            snippets = [s.strip() for s in snippets]
            snippets = [s[len('python'):] if s.startswith('python') else s for s in snippets]
            snippets = [s.strip() for s in snippets]
            snippets = dict(enumerate(snippets, start=1))
            if snippets:
                break
        else:
            raise RuntimeError('no code snippets after 3 tries')

        for i, s in snippets.items():
            print(f"[{i}]: {s}")

        selection = input('> ')
        if selection == 's':
            return
        if selection == '':
            selection = '1'
            print(f"Selected: [{selection}]")
        selection = int(selection)
        history_manager = IPython.get_ipython().history_manager
        history_manager.store_inputs(cls.line_num, snippets[selection].strip())
        cls.line_num += 1
        
    @classmethod
    def get_new_session(cls):
        return [
            {
                'role': 'system',
                'content': PROMPT
            },
            {
                'role': 'assistant',
                'content': "Understood"
            }
        ]

    @classmethod
    def get_current_session(cls):
        if cls.current_session is None:
            cls.current_session = cls.get_new_session()
        return cls.current_session

    line_num = 900000
    current_session = None
    _dummy = 1
    pass
