import logging
import sys
import threading
import yaml
from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentRegistry
from wiseagents.agents import PassThroughClientAgent, LLMOnlyWiseAgent
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
    while True:
        user_input = input("wise-agents (/help for available command): ")
        if  (user_input == '/help' or user_input == '/h'):
            print('/(l)oad-agents: Load agents from file')
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
            sys.exit(0)
        if (user_input == '/load-agents' or user_input == '/l'):
            file_path = input("Enter the file path (ENTER for default src/wiseagents/cli/test-multiple.yaml): ")
            if not file_path:
                file_path = "src/wiseagents/cli/test-multiple.yaml"
            with open(file_path) as stream:
                try:
                    for agent in yaml.load_all(stream, Loader=yaml.Loader):
                        agent : WiseAgent
                        print(f'Loaded agent: {agent.name}')
                        if agent.name == "PassThroughClientAgent1":
                            _passThroughClientAgent1 = agent
                            _passThroughClientAgent1.set_response_delivery(response_delivered)
                        agent.startAgent()
                except yaml.YAMLError as exc:
                    print(exc)
                print(f"registered agents= {WiseAgentRegistry.get_agents()}")
        if  (user_input == '/chat' or user_input == '/c'):
            while True:
                user_input = input("Enter a message (or /back): ")
                if  (user_input == '/back'):
                    break
                with cond:
                    _passThroughClientAgent1.send_request(WiseAgentMessage(user_input, "PassThroughClientAgent1"), "LLMOnlyWiseAgent2")
                    cond.wait()
        if (user_input == '/agents' or user_input == '/a'):
            print(f"registered agents= {WiseAgentRegistry.get_agents()}")

        if (user_input == '/send' or user_input == '/s'):
            agent_name = input("Enter the agent name: ")
            message = input("Enter the message: ")
            agent : WiseAgent = WiseAgentRegistry.get_agent(agent_name)
            if agent:
                with cond:
                    _passThroughClientAgent1.send_request(WiseAgentMessage(message, "PassThroughClientAgent1"), agent_name)
                    cond.wait()
            else:
                print(f"Agent {agent_name} not found")
    


if __name__ == "__main__":
    main()
