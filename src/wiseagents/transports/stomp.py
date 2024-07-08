import logging

import stomp.utils
from wiseagents import WiseAgentMessage,WiseAgentTransport
import stomp
import yaml

class WiseAgentRequestQueueListener(stomp.ConnectionListener):
    
    def __init__(self, transport: WiseAgentTransport):
        self.transport = transport
    
    def on_event(self, event):
        self.transport.event_receiver(event)
        
    def on_error(self, error):
        self.transport.error_receiver(error)

    def on_message(self, message: stomp.utils.Frame):
        logging.debug(f"Received message: {message}")
        logging.debug(f"Received message type: {message.__class__}")
        
        self.transport.request_receiver(yaml.load(message.body, yaml.Loader))

class WiseAgentResponseQueueListener(stomp.ConnectionListener):
    
    def __init__(self, transport: WiseAgentTransport):
        self.transport = transport
            
    def on_error(self, error):
        self.transport.error_receiver(error)

    def on_message(self, message: stomp.utils.Frame):
        logging.debug(f"Received message: {message}")
        logging.debug(f"Received message type: {message.__class__}")
        
        self.transport.response_receiver(yaml.load(message.body, yaml.Loader))


class StompWiseAgentTransport(WiseAgentTransport):
    
    yaml_tag = u'!wiseagents.transport.StompWiseAgentTransport'
    conn : stomp.Connection = None
    conn2 : stomp.Connection = None
    def __init__(self, host: str, port: int, username: str, password: str, agent_name: str):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._request_queue =  '/queue/request/' + agent_name
        self._response_queue =  '/queue/response/' + agent_name
        

    def __repr__(self) -> str:
        return super().__repr__() + f"host={self._host}, port={self._port}, username={self._username}, password={self._password}, destination={self.destination}"

    def __getstate__(self) -> object:
        '''Return the state of the transport. Removing the instance variable chain to avoid it is serialized/deserialized by pyyaml.'''
        state = self.__dict__.copy()
        del state['conn']
        del state['conn2']
        del state['_message_receiver']
        del state['_event_receiver']
        del state['_error_receiver']
        return state 


    def start(self):
        hosts = [(self.host, self.port)] 
        self.conn = stomp.Connection(host_and_ports=hosts)
        self.conn.set_listener('WiseAgentRequestTopicListener', WiseAgentRequestQueueListener(self))
        #self.conn.start()
        self.conn.connect(self.username, self.password, wait=True)
        #self.conn.connect(self.username, self.password, wait=True, host=self.host, port=self.port)
        self.conn.subscribe(destination=self.request_queue, id=id(self), ack='auto')
        
        self.conn2 = stomp.Connection(host_and_ports=hosts)
        
        self.conn2.set_listener('WiseAgentResponseQueueListener', WiseAgentResponseQueueListener(self))
        self.conn2.connect(self.username, self.password, wait=True)
        
        self.conn2.subscribe(destination=self.response_queue, id=id(self) + 1 , ack='auto')


    def send_request(self, message: WiseAgentMessage, dest_agent_name: str):
        # Send the message using the STOMP protocol
        if self.conn is None or self.conn2 is None:
            self.start()
        request_destination = '/queue/request/' + dest_agent_name    
        self.conn.send(body=yaml.dump(message), destination=request_destination)
        
    def send_response(self, message: WiseAgentMessage, dest_agent_name: str):
        # Send the message using the STOMP protocol
        if self.conn is None or self.conn2 is None:
            self.start()
        response_destination = '/queue/response/' + dest_agent_name    
        self.conn2.send(body=yaml.dump(message), destination=response_destination)

    def stop(self):
        if self.conn is not None:
            #unsubscribe from the request topic
            self.conn.unsubscribe(destination=self._request_topic)
            #unsubscribe from the response queue
            self.conn2.unsubscribe(destination=self._response_queue)
            # Disconnect from the STOMP server
            self.conn.disconnect()
            self.conn2.disconnect()
            
        
    @property
    def host(self) -> str:
        return self._host
    @property
    def port(self) -> int:
        return self._port
    @property
    def username(self) -> str:
        return self._username
    @property
    def password(self) -> str:
        return self._password
    @property
    def request_queue(self) -> str:
        return self._request_queue
    @property
    def response_queue(self) -> str:
        return self._response_queue
    
    