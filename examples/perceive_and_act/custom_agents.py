import os
import threading
import time
from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessageParam
from typing import List, Optional
from wiseagents import WiseAgent, WiseAgentEvent, WiseAgentMessage, WiseAgentTransport
from wiseagents.yaml import WiseAgentsLoader

class PerceivingAgent(WiseAgent):
    yaml_tag = u'!custom_agents.PerceivingAgent'
    yaml_loader = WiseAgentsLoader

    stop_event = threading.Event()

    def __init__(self, name: str, description: str, transport: WiseAgentTransport, file_path: str, check_interval: float, destination_agent_name: str):
        self._file_path = file_path
        self._check_interval = check_interval
        self._destination_agent_name = destination_agent_name
        super().__init__(name=name, description=description, transport=transport)

    def start_agent(self):
        super().start_agent()
        self.stop_event.clear()
        self.perceive(self._file_path, self.on_file_change, self._check_interval)

    def stop_agent(self):
        self.stop_event.set()
        super().stop_agent()

    def process_request(self, request: WiseAgentMessage,
            conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
         pass

    def process_response(self, response: WiseAgentMessage):
        pass
    
    def process_event(self, event: WiseAgentEvent):
        pass
    
    def process_error(self, error: WiseAgentMessage):
        pass

    def perceive(self, file_path, callback, check_interval=1.0):
        """
        Monitors a file for any changes and invokes a callback with the file's content upon modification.

        
        Args:
            file_path (str): The path to the file to monitor.
            callback (callable): A function to call with the file's content when it changes.
            check_interval (float, optional): Time in seconds between checks. Defaults to 1.0.
        """
        def watch():
            try:
                last_mtime = os.path.getmtime(file_path)
            except FileNotFoundError:
                last_mtime = None

            while not self.stop_event.is_set():
                try:
                    print(f"Checking file {file_path}")
                    current_mtime = os.path.getmtime(file_path)
                    if last_mtime is None:
                        last_mtime = current_mtime
                    elif current_mtime != last_mtime:
                        print(f"File {file_path} has changed")
                        last_mtime = current_mtime
                        with open(file_path, 'r') as f:
                            content = f.read()
                        callback(content)
                except FileNotFoundError:
                    if last_mtime is not None:
                        last_mtime = None
                except Exception as e:
                    print(f"Error monitoring file: {e}")
                time.sleep(check_interval)
        
        thread = threading.Thread(target=watch, daemon=True)
        thread.start()

    def on_file_change(self, content):
        print(f"sending message: {content}, {self.name}, {self._destination_agent_name}")
        self.send_request(WiseAgentMessage(content, self.name), self._destination_agent_name)

class ActionAgent(WiseAgent):
    yaml_tag = u'!custom_agents.ActionAgent'
    yaml_loader = WiseAgentsLoader

    def __init__(self, name: str, description: str, transport: WiseAgentTransport, destination_file_path: str):
        self._destination_file_path = destination_file_path
        super().__init__(name=name, description=description, transport=transport)

    def start_agent(self):
        super().start_agent()

    def process_request(self, request: WiseAgentMessage, conversation_history: List[ChatCompletionMessageParam]) -> str | None:
        with open(self._destination_file_path, 'w') as f:
            f.write(request.message)
        self.send_response(WiseAgentMessage("File updated", self.name), request.sender)


    def process_response(self, response: WiseAgentMessage):
        pass
    
    def process_event(self, event: WiseAgentEvent):
        pass
    
    def process_error(self, error: WiseAgentMessage):
        pass    