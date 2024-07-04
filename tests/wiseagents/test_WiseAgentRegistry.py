from wiseagents import WiseAgentContext, WiseAgentRegistry, WiseAgent

   
def test_register_agents():
    agent = WiseAgent(name="Agent1", description="This is a test agent")
    WiseAgentRegistry.register_agent(agent)
    assert 1 == WiseAgentRegistry.get_agents().__len__()
    assert agent == WiseAgentRegistry.get_agent(agent.name)

def test_remove_agent():
    agent = "Agent1"
    agent = WiseAgent(name="Agent1", description="This is a test agent")
    WiseAgentRegistry.remove_agent(agent.name)
    assert None == WiseAgentRegistry.get_agent(agent.name)

def test_get_agents():
    WiseAgentRegistry.clear_agents()
    agents = [WiseAgent(name="Agent1", description="This is a test agent"), 
              WiseAgent(name="Agent2", description="This is another test agent"), 
              WiseAgent(name="Agent3", description="This is yet another test agent")]
    for agent in agents:
        WiseAgentRegistry.register_agent(agent)
    
    for agent in agents:
        assert agent == WiseAgentRegistry.get_agent(agent.name)

def test_get_contexts():
    WiseAgentRegistry.clear_contexts()
    contexts = [WiseAgentContext(name="Context1"), 
              WiseAgentContext(name="Context2"), 
              WiseAgentContext(name="Context3")]
    for context in contexts:
        WiseAgentRegistry.register_context(context)
    
    for context in contexts:
        assert context == WiseAgentRegistry.get_context(context.name)
        
def test_get_or_create_context():
    WiseAgentRegistry.clear_contexts()
    context = WiseAgentContext(name="Context1")
    WiseAgentRegistry.get_or_create_context(context.name)
    assert context == WiseAgentRegistry.get_context(context.name)