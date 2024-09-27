import importlib
import signal
import sys
import threading
import traceback
from typing import List
from wiseagents.yaml import WiseAgentsLoader

import yaml

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentRegistry
# These unsued imports are need for yaml.load_all. If they are removed, the yaml.load_all will not find the constructors for these classes
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

def signal_handler(sig, frame):
    global user_question_agent
    print('You pressed Ctrl+C! Please wait for the agents to stop')
    for agent in agent_list:
        print(f"Stopping agent {agent.name}")
        agent.stop_agent()
    exit(0)


    

def main():
    global agent_list
    agent_list = []
    user_input = "h"
    file_path = None
    default_file_path = "src/wiseagents/cli/test-multiple.yaml"

    signal.signal(signal.SIGINT, signal_handler)
    
    if (sys.argv.__len__() > 1):
            user_input="/load-agents"
            file_path=sys.argv[1]
    while True:
        if  (user_input == '/help' or user_input == '/h'):
            print('/(l)oad-agents: Load agents from file')
            print('/(r)eload agents: Reload agents from file')
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
            print('/exit seceleted! Please wait for the agents to stop')
            for agent in agent_list:
                print(f"Stopping agent {agent.name}")
                agent.stop_agent()
            sys.exit(0)
        if (user_input == '/reload-agents' or user_input == '/r'):
            for agent in agent_list:
                agent.stop_agent()
            reload_path = input(f'Enter the file path (ENTER for default {file_path} ): ')
            if reload_path:
                file_path = reload_path
            user_input = '/load-agents'
        if (user_input == '/load-agents' or user_input == '/l'):
            if not file_path:
                file_path = input(f'Enter the file path (ENTER for default {default_file_path} ): ')
                if not file_path:
                    file_path = default_file_path
            with open(file_path) as stream:
                try:  

                    for agent in yaml.load_all(stream, Loader=WiseAgentsLoader):
                        agent : WiseAgent
                        print(f'Loaded agent: {agent.name}')
                        if agent.name == "PassThroughClientAgent1":
                            _passThroughClientAgent1 = agent
                            _passThroughClientAgent1.set_response_delivery(response_delivered)
                        agent.start_agent()
                        agent_list.append(agent)
                except yaml.YAMLError as exc:
                    traceback.print_exc()
                print(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
        if  (user_input == '/chat' or user_input == '/c'):
            while True:
                user_input = input("Enter a message (or /back): ")
                if  (user_input == '/back'):
                    break
                with cond:
                    _passThroughClientAgent1.send_request(WiseAgentMessage(user_input, "PassThroughClientAgent1"), "LLMOnlyWiseAgent2")
                    cond.wait()
        if (user_input == '/agents' or user_input == '/a'):
            print(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")

        if (user_input == '/send' or user_input == '/s'):
            agent_name = input("Enter the agent name: ")
            message = input("Enter the message: ")
            agent : WiseAgent = WiseAgentRegistry.get_agent_metadata(agent_name)
            if agent:
                with cond:
                    _passThroughClientAgent1.send_request(WiseAgentMessage(message, "PassThroughClientAgent1"), agent_name)
                    cond.wait()
            else:
                print(f"Agent {agent_name} not found")
        user_input = input("wise-agents (/help for available commands): ")
        
    


if __name__ == "__main__":
    main()
