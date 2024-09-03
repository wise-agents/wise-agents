import logging
import os
import traceback

import stomp.utils
from wiseagents import WiseAgentMessage,WiseAgentTransport
import stomp
import yaml

class WiseAgentRequestQueueListener(stomp.ConnectionListener):
    '''A listener for the request queue.'''
    
    def __init__(self, transport: WiseAgentTransport):
        '''Initialize the listener.

        Args:
            '''
        self.transport = transport
    
    def on_event(self, event):
        '''Handle an event.'''
        self.transport.event_receiver(event)
        
    def on_error(self, error):
        '''Handle an error.'''
        self.transport.error_receiver(error)

    def on_message(self, message: stomp.utils.Frame):
        '''Handle a message.'''
        logging.debug(f"{self}: Received message: {message}")
        logging.debug(f"Received message type: {message.__class__}")
        logging.debug(f"Calling the callback function: {self.transport.request_receiver}")
        self.transport.request_receiver(yaml.load(message.body, yaml.Loader))

class WiseAgentResponseQueueListener(stomp.ConnectionListener):
    '''A listener for the response queue.'''
    def __init__(self, transport: WiseAgentTransport):
        '''Initialize the listener.

        Args:
            transport (WiseAgentTransport): the transport'''
        self.transport = transport
            
    def on_error(self, error):
        '''Handle an error.'''
        self.transport.error_receiver(error)

    def on_message(self, message: stomp.utils.Frame):
        '''Handle a message.'''
        logging.debug(f"Received message: {message}")
        logging.debug(f"Received message type: {message.__class__}")
        
        self.transport.response_receiver(yaml.load(message.body, yaml.Loader))


class StompWiseAgentTransport(WiseAgentTransport):
    '''A transport for sending messages between agents using the STOMP protocol.'''
    
    yaml_tag = u'!wiseagents.transport.StompWiseAgentTransport'
    request_conn : stomp.Connection = None
    response_conn : stomp.Connection = None
    def __init__(self, host: str, port: int, agent_name: str):
        '''Initialize the transport.

        Args:
            host (str): the host
            port (int): the port
            agent_name (str): the agent name'''
        self._host = host
        self._port = port
        self._agent_name = agent_name
        

    def __repr__(self) -> str:
        return super().__repr__() + f"host={self._host}, port={self._port}, agent_name={self._agent_name}"

    def __getstate__(self) -> object:
        '''Return the state of the transport. Removing the instance variable chain to avoid it is serialized/deserialized by pyyaml.'''
        state = self.__dict__.copy()
        del state['_request_receiver']
        del state['_response_receiver']
        del state['_event_receiver']
        del state['_error_receiver']
        del state['request_conn']
        del state['response_conn']
        return state 


    def start(self):
        '''
        Start the transport.
        require the environment variables STOMP_USER and STOMP_PASSWORD to be set'''
        if (self.request_conn is not None and self.request_conn.is_connected()) or (self.response_conn is not None and self.response_conn.is_connected()):
            return
        hosts = [(self.host, self.port)] 
        self.request_conn = stomp.Connection(host_and_ports=hosts, heartbeats=(60000, 60000))
        self.request_conn.set_listener('WiseAgentRequestTopicListener', WiseAgentRequestQueueListener(self))
        self.request_conn.connect(os.getenv("STOMP_USER"), os.getenv("STOMP_PASSWORD"), wait=True)
        self.request_conn.subscribe(destination=self.request_queue, id=id(self), ack='auto')
        
        self.response_conn = stomp.Connection(host_and_ports=hosts, heartbeats=(60000, 60000))
        
        self.response_conn.set_listener('WiseAgentResponseQueueListener', WiseAgentResponseQueueListener(self))
        self.response_conn.connect(os.getenv("STOMP_USER"), os.getenv("STOMP_PASSWORD"), wait=True)
        
        self.response_conn.subscribe(destination=self.response_queue, id=id(self) + 1 , ack='auto')


    def send_request(self, message: WiseAgentMessage, dest_agent_name: str):
        '''Send a request message to an agent.

        Args:
            message (WiseAgentMessage): the message to send
            dest_agent_name (str): the destination agent name'''
        # Send the message using the STOMP protocol
        if self.request_conn is None or self.response_conn is None:
            self.start()
        if self.request_conn.is_connected() == False:
            self.request_conn.connect(os.getenv("STOMP_USER"), os.getenv("STOMP_PASSWORD"), wait=True)
        if self.response_conn.is_connected() == False:
            self.response_conn.connect(os.getenv("STOMP_USER"), os.getenv("STOMP_PASSWORD"), wait=True)
        request_destination = '/queue/request/' + dest_agent_name
        logging.debug(f"Sending request {message} to {request_destination}")    
        self.request_conn.send(body=yaml.dump(message), destination=request_destination)
        
    def send_response(self, message: WiseAgentMessage, dest_agent_name: str):
        '''Send a response message to an agent.

        Args:
            message (WiseAgentMessage): the message to send
            dest_agent_name (str): the destination agent name'''
        # Send the message using the STOMP protocol
        if self.request_conn is None or self.response_conn is None:
            self.start()
        response_destination = '/queue/response/' + dest_agent_name    
        self.response_conn.send(body=yaml.dump(message), destination=response_destination)

    def stop(self):
        '''Stop the transport.'''
        if self.request_conn is not None:
            #unsubscribe from the request topic
            self.request_conn.unsubscribe(destination=self.request_queue, id=id(self))
            #unsubscribe from the response queue
            self.response_conn.unsubscribe(destination=self.response_queue, id=id(self) + 1)
            # Disconnect from the STOMP server
            self.request_conn.disconnect()
            self.response_conn.disconnect()
            
        
    @property
    def host(self) -> str:
        '''Get the host.'''
        return self._host
    @property
    def port(self) -> int:
        '''Get the port.'''
        return self._port
    @property
    def agent_name(self) -> str:
        '''Get the agent name.'''
        return self._agent_name
    @property
    def request_queue(self) -> str:
        '''Get the request queue.'''
        return '/queue/request/' + self.agent_name
    @property
    def response_queue(self) -> str:
        '''Get the response queue.'''
        return '/queue/response/' + self.agent_name
    
    