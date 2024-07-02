from langchain_community.graphs.graph_document import (GraphDocument as LangChainGraphDocument,
                                                       Relationship as LangChainRelationship, Node)
from langchain_core.documents import Document as LangChainDocument
from wiseagents.graphdb import Source
from wiseagents.graphdb.Entity import Entity
from wiseagents.graphdb.GraphDocument import GraphDocument
from wiseagents.graphdb.Relationship import Relationship
from wiseagents.graphdb.WiseAgentGraphDB import WiseAgentGraphDB


class LangChainWiseAgentGraphDB(WiseAgentGraphDB):

    def convert_to_lang_chain_node(self, entity: Entity) -> Node:
        return Node(id=entity.id, type=entity.label, properties=entity.metadata)

    def convert_to_lang_chain_relationship(self, relationship: Relationship) -> LangChainRelationship:
        return LangChainRelationship(source=self.convert_to_lang_chain_node(relationship.source),
                                     target=self.convert_to_lang_chain_node(relationship.target),
                                     type=relationship.label,
                                     properties=relationship.metadata)

    def convert_to_lang_chain_graph_document(self, graph_document: GraphDocument) -> LangChainGraphDocument:
        return LangChainGraphDocument(nodes=[self.convert_to_lang_chain_node(entity)
                                             for entity in graph_document.entities],
                                      relationships=[self.convert_to_lang_chain_relationship(relationship)
                                                     for relationship in graph_document.relationships],
                                      source=self.convert_to_lang_chain_document(graph_document.source))

    def convert_to_lang_chain_document(self, source: Source) -> LangChainDocument:
        return LangChainDocument(id=source.id, page_content=source.content, metadata=source.metadata)




