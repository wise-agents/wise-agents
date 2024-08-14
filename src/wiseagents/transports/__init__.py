# This is the __init__.py file for the wiseagents.transports package

# Import any modules or subpackages here

# Define any necessary initialization code here

from wiseagents.transports.stomp import StompWiseAgentTransport


# Optionally, you can define __all__ to specify the public interface of the package
__all__ = ['StompWiseAgentTransport']
''' A package for creating and managing transport that use the STOMP protocol.
Export the following classes:
StompWiseAgentTransport: a transport for agents that uses the STOMP protocol.'''
