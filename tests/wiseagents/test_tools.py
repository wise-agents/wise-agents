import json
import logging
import threading

from wiseagents import WiseAgentMessage, WiseAgentRegistry, WiseAgentTool
from wiseagents.llm.openai_API_wise_agent_LLM import OpenaiAPIWiseAgentLLM
from wiseagents.transports.stomp import StompWiseAgentTransport
from wiseagents.wise_agent_impl import LLMWiseAgentWithTools, PassThroughClientAgent


cond = threading.Condition()

def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
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
        print(f"C Response delivered: {msg}")
        cond.notify()

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
   
   WiseAgentTool(name="get_current_weather", description="Get the current weather in a given location",
                 parameters_json_schema=json_schema, call_back=get_current_weather) 
   llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                         model_name="Phi-3-mini-4k-instruct-q4.gguf")      
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
   