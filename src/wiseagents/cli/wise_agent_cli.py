import sys
import threading
import traceback
from typing import List

import yaml

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentRegistry
#these unsued imports are need for yaml.load_all. If they are removed, the yaml.load_all will not find the constructors for these classes 
import wiseagents.agents
from wiseagents.transports import StompWiseAgentTransport

cond = threading.Condition()

global _passThroughClientAgent1

def response_delivered(message: WiseAgentMessage):
    with cond: 
        response = message.message
        msg = response
        print(f"C Response delivered: {msg}")
        cond.notify()


def main():
    agent_list : List[WiseAgent]= []
    user_input = "h"
    file_path = None
    if (sys.argv.__len__() > 1):
            user_input="/load-agents"
            file_path=sys.argv[1]
    while True:
        if  (user_input == '/help' or user_input == '/h'):
            print('/(l)oad-agents: Load agents from file')
            print('/(r)load agents: Reload agents from file')
            print('/(c)hat: Start a chat')
            print('/(t)race: Show the message trace')
            print('/e(x)it: Exit the application')
            print('/(h)elp: Show the available commands')
            print('(a)gents: Show the registered agents')
            print('(s)end: Send a message to an agent')
            
        if (user_input == '/trace' or user_input == '/t'):
            for msg in WiseAgentRegistry.get_or_create_context('default').message_trace:
                print(msg)
        if  (user_input == '/exit' or user_input == '/x'):
            #stop all agents
            for agent in agent_list:
                agent.stop_agent()
            sys.exit(0)
        if (user_input == '/load-agents' or user_input == '/l'):
            if not file_path:
                file_path = input("Enter the file path (ENTER for default src/wiseagents/cli/test-multiple.yaml): ")
                if not file_path:
                    file_path = "src/wiseagents/cli/test-multiple.yaml"
            with open(file_path) as stream:
                try:
                    for agent in yaml.load_all(stream, Loader=yaml.FullLoader):
                        agent : WiseAgent
                        print(f'Loaded agent: {agent.name}')
                        if agent.name == "PassThroughClientAgent1":
                            _passThroughClientAgent1 = agent
                            _passThroughClientAgent1.set_response_delivery(response_delivered)
                        agent.start_agent()
                        agent_list.append(agent)
                except yaml.YAMLError as exc:
                    traceback.print_exc()
                print(f"registered agents= {WiseAgentRegistry.fetch_agents_descriptions_dict()}")
        if  (user_input == '/chat' or user_input == '/c'):
            while True:
                user_input = input("Enter a message (or /back): ")
                if  (user_input == '/back'):
                    break
                with cond:
                    _passThroughClientAgent1.send_request(WiseAgentMessage(user_input, "PassThroughClientAgent1"), "LLMOnlyWiseAgent2")
                    cond.wait()
        if (user_input == '/agents' or user_input == '/a'):
            print(f"registered agents= {WiseAgentRegistry.fetch_agents_descriptions_dict()}")

        if (user_input == '/send' or user_input == '/s'):
            agent_name = input("Enter the agent name: ")
            message = input("Enter the message: ")
            agent : WiseAgent = WiseAgentRegistry.get_agent_description(agent_name)
            if agent:
                with cond:
                    _passThroughClientAgent1.send_request(WiseAgentMessage(message, "PassThroughClientAgent1"), agent_name)
                    cond.wait()
            else:
                print(f"Agent {agent_name} not found")
        user_input = input("wise-agents (/help for available command): ")
        
    


if __name__ == "__main__":
    main()
