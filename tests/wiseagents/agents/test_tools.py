import json
import logging
import os
import threading

import pytest

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentRegistry, WiseAgentTool
from wiseagents.agents import LLMWiseAgentWithTools, PassThroughClientAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports.stomp import StompWiseAgentTransport


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    
    


cond = threading.Condition()
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "22", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps(
            {"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"}
        )
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "25", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})
    
    


def response_delivered(message: WiseAgentMessage):
    with cond: 
        response = message.message
        msg = response
        assert "22" in msg 
        print(f"C Response delivered: {msg}")
        cond.notify()


class WiseAgentWeather(WiseAgent):
     
    request_received : WiseAgentMessage = None
    response_received : WiseAgentMessage = None
    
    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description
        transport = StompWiseAgentTransport(host='localhost', port=61616, agent_name=self.name)
        super().__init__(name, description, transport, None, None, None)
        
        
    def process_event(self, event):
        return True
    def process_error(self, error):
        logging.error(error)
        return True
    def handle_request(self, request: WiseAgentMessage):
        self.request_received = request
        logging.info(f"Received request: {request.message}")
        function_args = json.loads(request.message)
        logging.info(f"Function args: {function_args}")
        response = get_current_weather(**function_args)
        response_message = WiseAgentMessage(message=json.dumps(response), sender=self.name, 
                                            chat_id=request.chat_id, tool_id=request.tool_id, 
                                            context_name=request.context_name, 
                                            route_response_to=request.route_response_to)
        logging.info(f"Sending response: {response_message}")
        self.send_response(response_message, request.sender )
        return True
    def process_response(self, response : WiseAgentMessage):
        self.response_received = response
        return True

    def stop(self):
        pass    



#Note: this test work using ollama as inference system and llama3.1 as model
#Install ollam from their official website https://ollama.com/
#run ollama with the following command: ollama run llama3.1

@pytest.mark.needsllm
def test_agent_tool():
    try:
        json_schema = {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                        }
        WiseAgentTool(name="WeatherAgent", description="Get the current weather in a given location", agent_tool=True,
                    parameters_json_schema=json_schema, call_back=None) 
        llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="llama3.1",
                                            remote_address="http://localhost:11434/v1")      
        
        weather_agent = WiseAgentWeather(name="WeatherAgent", description="Get the current weather in a given location")
        
        agent = LLMWiseAgentWithTools(name="WiseIntelligentAgent",
                                    description="This is a test agent",
                                    llm=llm,
                                    tools = ["WeatherAgent"],
                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="WiseIntelligentAgent")
                                    )
    
        logging.info(f"tool: {WiseAgentRegistry.get_tool('WeatherAgent').get_tool_OpenAI_format()}")
        with cond:    

            client_agent1  = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                    )
            client_agent1.set_response_delivery(response_delivered)
            client_agent1.send_request(WiseAgentMessage("What is the current weather in Tokyo?", "PassThroughClientAgent1"), 
                                                        "WiseIntelligentAgent")
            cond.wait()
            

        logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_descriptions_dict()}")
        for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
            logging.debug(f'{message}')
    finally:
        client_agent1.stop_agent()    
        agent.stop_agent()
        weather_agent.stop_agent()
    
@pytest.mark.needsllm
def test_tool():
    try:
        json_schema = {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                        }
        WiseAgentTool(name="get_current_weather", description="Get the current weather in a given location", agent_tool=False,
                    parameters_json_schema=json_schema, call_back=get_current_weather) 
        llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="llama3.1",
                                            remote_address="http://localhost:11434/v1")      
        agent = LLMWiseAgentWithTools(name="WiseIntelligentAgent",
                                    description="This is a test agent",
                                    llm=llm,
                                    tools = ["get_current_weather"],
                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="WiseIntelligentAgent")
                                    )
    
        logging.info(f"tool: {WiseAgentRegistry.get_tool('get_current_weather').get_tool_OpenAI_format()}")
        with cond:    

            client_agent1  = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                    )
            client_agent1.set_response_delivery(response_delivered)
            client_agent1.send_request(WiseAgentMessage("What is the current weather in Tokyo?", "PassThroughClientAgent1"), 
                                                        "WiseIntelligentAgent")
            cond.wait()
            

        logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_descriptions_dict()}")
        for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
            logging.debug(f'{message}')
    finally:
        client_agent1.stop_agent()
        agent.stop_agent()
