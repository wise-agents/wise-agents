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
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()

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
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
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
    def process_request(self, request: WiseAgentMessage):
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
    def get_recipient_agent_name(self, message):
        return self.name
    def stop(self):
        pass    



#Note: this test work using GROQ as inference system and llama3.1 as model
#You need to set the environment variable GROQ_API_KEY with the value of your OpenAI API key
#get your GROQ API key from https://groq.com/ and set it in the environment variable GROQ_API_KEY
def test_agent_tool():
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
    
    weather_agent = WiseAgentWeather(name="WeatherAgent", description="Get the current weather in a given location")
    weather_agent.startAgent()
    agent = LLMWiseAgentWithTools(name="WiseIntelligentAgent",
                                 description="This is a test agent",
                                 llm=llm,
                                 tools = ["WeatherAgent"],
                                 transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="WiseIntelligentAgent")
                                 )
    agent.startAgent() 
   
    logging.info(f"tool: {WiseAgentRegistry.get_tool('WeatherAgent').get_tool_OpenAI_format()}")
    with cond:    

        client_agent1  = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                )
        client_agent1.set_response_delivery(response_delivered)
        client_agent1.send_request(WiseAgentMessage("What is the current weather in Tokyo?", "PassThroughClientAgent1"), 
                                                    "WiseIntelligentAgent")
        cond.wait()
        

    for agent in WiseAgentRegistry.get_agents():
        logging.info(f"Agent: {agent}")
    for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
        logging.info(f'{message.sender} : {message.message} ')


@pytest.mark.needsllm
def test_tool():
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
    agent.startAgent() 
   
    logging.info(f"tool: {WiseAgentRegistry.get_tool('get_current_weather').get_tool_OpenAI_format()}")
    with cond:    

        client_agent1  = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                )
        client_agent1.set_response_delivery(response_delivered)
        client_agent1.send_request(WiseAgentMessage("What is the current weather in Tokyo?", "PassThroughClientAgent1"), 
                                                    "WiseIntelligentAgent")
        cond.wait()
        

    for agent in WiseAgentRegistry.get_agents():
        logging.info(f"Agent: {agent}")
    for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
        logging.info(f'{message.sender} : {message.message} ')
    
