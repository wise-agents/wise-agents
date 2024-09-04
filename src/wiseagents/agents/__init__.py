# This is the __init__.py file for the wiseagents.agents package

# Import any modules or subpackages here

# Define any necessary initialization code here

# Optionally, you can define __all__ to specify the public interface of the package
# __all__ = ['module1', 'module2', 'subpackage']
from .collaboration_wise_agents import CollaboratorWiseAgent, PhasedCoordinatorWiseAgent, SequentialCoordinatorWiseAgent
from .rag_wise_agents import CoVeChallengerRAGWiseAgent, GraphRAGWiseAgent, RAGWiseAgent

__all__ = ['CollaboratorWiseAgent', 'PhasedCoordinatorWiseAgent', 'SequentialCoordinatorWiseAgent', 'RAGWiseAgent',
           'GraphRAGWiseAgent', 'CoVeChallengerRAGWiseAgent']
