import json
import logging
import os
import threading

import pytest

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentMetaData, WiseAgentRegistry, WiseAgentTool
from wiseagents.agents import LLMWiseAgentWithTools, PassThroughClientAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports.stomp import StompWiseAgentTransport
from tests.wiseagents import assert_standard_variables_set


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    assert_standard_variables_set()
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
    elif "milan" in location.lower():
        return json.dumps({"location": "Milan", "temperature": "27", "unit": "celsius"})
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
    
    def __init__(self, name: str, metadata: WiseAgentMetaData):
        transport = StompWiseAgentTransport(host='localhost', port=61616, agent_name=name)
        super().__init__(name, metadata, transport, None, None, None)
        
        
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
                                            tool_id=request.tool_id, 
                                            context_name=request.context_name, 
                                            route_response_to=request.route_response_to)
        logging.info(f"Sending response: {response_message} to {request.sender}")
        self.send_response(response_message, request.sender )
        return True
    def process_response(self, response : WiseAgentMessage):
        self.response_received = response
        return True

    def stop(self):
        pass    



#Note: this test work using GROQ as inference system and llama3.1 as model
#You need to set the environment variable GROQ_API_KEY with the value of your OpenAI API key
#get your GROQ API key from https://groq.com/ and set it in the environment variable GROQ_API_KEY
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
        groq_api_key= os.getenv("GROQ_API_KEY")
        assert groq_api_key is not None
        llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="llama-3.1-70b-versatile",
                                            remote_address="https://api.groq.com/openai/v1",
                                            api_key=groq_api_key)      
        
        weather_agent = WiseAgentWeather(name="WeatherAgent", metadata=WiseAgentMetaData(description="Get the current weather in a given location"))
        agent = LLMWiseAgentWithTools(name="WiseIntelligentAgent",
                                    metadata=WiseAgentMetaData(description="This is a test agent"),
                                    llm=llm,
                                    tools = ["WeatherAgent"],
                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="WiseIntelligentAgent")
                                    )
        logging.info(f"tool: {WiseAgentRegistry.get_tool('WeatherAgent').get_tool_OpenAI_format()}")
        WiseAgentRegistry.create_context("default")
        with cond:    

            client_agent1  = PassThroughClientAgent(name="PassThroughClientAgent1", metadata=WiseAgentMetaData(description="This is a test agent"),
                                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                    )
            client_agent1.set_response_delivery(response_delivered)
            client_agent1.send_request(WiseAgentMessage(message="What is the current weather in Tokyo?", sender="PassThroughClientAgent1",context_name="default"), 
                                                        "WiseIntelligentAgent")
            cond.wait(timeout=300)
            

        logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
        for message in WiseAgentRegistry.get_context('default').message_trace:
            logging.debug(f'{message}')
    finally:
        client_agent1.stop_agent()
        agent.stop_agent()
        weather_agent.stop_agent()
        WiseAgentRegistry.remove_context("default")


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
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                            api_key=groq_api_key)      
        agent = LLMWiseAgentWithTools(name="WiseIntelligentAgent",
                                    metadata=WiseAgentMetaData(description="This is a test agent"),
                                    llm=llm,
                                    tools = ["get_current_weather"],
                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="WiseIntelligentAgent")
                                    )
        
        logging.info(f"tool: {WiseAgentRegistry.get_tool('get_current_weather').get_tool_OpenAI_format()}")
        WiseAgentRegistry.create_context("default")
        with cond:    

            client_agent1  = PassThroughClientAgent(name="PassThroughClientAgent1", metadata=WiseAgentMetaData(description="This is a test agent"),
                                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                    )
            client_agent1.set_response_delivery(response_delivered)
            client_agent1.send_request(WiseAgentMessage(message="What is the current weather in Tokyo?", sender="PassThroughClientAgent1",context_name="default"), 
                                                        "WiseIntelligentAgent")
            cond.wait(timeout=300)
            

        logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
        for message in WiseAgentRegistry.get_context('default').message_trace:
            logging.debug(f'{message}')
    finally:
        client_agent1.stop_agent()
        agent.stop_agent()
        WiseAgentRegistry.remove_context("default")
   
    
