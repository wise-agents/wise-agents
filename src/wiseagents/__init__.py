# This is the __init__.py file for the wiseagents package

# Import any modules or subpackages here

from wiseagents.wise_agent import WiseAgentContext
from wiseagents.wise_agent import WiseAgent
from wiseagents.wise_agent import WiseAgentRegistry
from wiseagents.wise_agent import WiseAgentTool
from wiseagents.wise_agent_messaging import WiseAgentMessage
from wiseagents.wise_agent_messaging import WiseAgentMessageType
from wiseagents.wise_agent_messaging import WiseAgentTransport
from wiseagents.wise_agent_messaging import WiseAgentEvent

# Define any necessary initialization code here

# Optionally, you can define __all__ to specify the public interface of the package
# __all__ = ['module1', 'module2', 'subpackage']
__all__ = ['WiseAgentRegistry', 'WiseAgentContext', 'WiseAgent', 'WiseAgentTool',
           'WiseAgentMessage', 'WiseAgentMessageType', 'WiseAgentTransport', 'WiseAgentEvent']

''' A package for creating and managing agents. 
    Each agent is a separate entity that can send and receive messages.
    Agents can be created, started, stopped, and removed.
    Agents can send and receive messages.
    Agents can be assigned to tools.
    Exports the following classes:
    WiseAgentRegistry: a registry for managing agents.
    WiseAgentContext: a context for an agent.
    WiseAgent: a base class for agents.
    WiseAgentTool: a tool for agents.
    WiseAgentMessage: a message for agents.
    WiseAgentMessageType: a message type for agents.
    WiseAgentTransport: a transport for agents.
    WiseAgentEvent: an event for agents.'''