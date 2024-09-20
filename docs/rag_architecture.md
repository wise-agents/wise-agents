# Using Retrieval Augmented Generation (RAG) with Wise Agents

Wise Agents provides agent implementations that can be used for both standard retrieval augmented
generation (RAG) and also for RAG with knowledge graphs (Graph RAG).

## What is RAG?

Retrieval augmented generation (RAG) provides the ability to enhance the knowledge of a large language
model (LLM) by incorporating additional information during response generation. This is very important
because although LLMs are trained with extremely large quantities of data, this data is static, has
a cut-off date, and likely lacks domain-specific information. RAG provides the ability to incorporate
additional information obtained from knowledge sources to ground LLM responses using this information,
resulting in better quality responses.

### How does RAG work?

To be able to make use of RAG, the very first step is ingestion. Here, knowledge sources are processed,
split into chunks of text, each chunk of text is converted to a vector representation (also known as
an embedding), and then stored in a vector database.

After this initial step, upon receiving a query, the goal is to retrieve the information that is most
relevant to the query from the vector database. This is done by converting the query to a vector
representation (i.e., embedding) and then querying the vector database to retrieve the chunks that
are most similar to the query.

The retrieved information is then included in a prompt to the LLM along with the original query. This
helps the LLM to generate a response that is grounded in the retrieved information.

### Our implementation

Wise Agents provides a `wiseagents.agents.RAGWiseAgent` that you can use or extend to answer questions
using RAG.

#### Vector Database Integration

A `RAGWiseAgent` makes use of a `wiseagents.vectordb.WiseAgentVectorDB`, which provides integration
with a vector database. Wise Agents provides an implementation of this abstract class that makes use
of `pgvector`, see `wiseagents.vectordb.PGVectorLangChainWiseAgentVectorDB`. We are planning on adding
integration with additional vector databases in the future. You can also create your own implementations
depending on the vector database you'd like to use.

## What is Graph RAG?

Graph RAG is a more structured approach to RAG. In standard RAG, as described above, the knowledge
sources are simply split into chunks of text. However, there are many sources of information that
actually have a lot of structure to them where this structure would be lost if just convert the knowledge
source to text as is and split into chunks. For example, think about a bug report that has many different
fields like "Description", "Steps to Reproduce", "Relates To", "Resolution", etc. If we just take the text
from the bug report as is and just split the text into chunks, we'd lose all the structure that is
inherently present in the bug report and the relationships to other bug reports.

Graph RAG involves converting knowledge sources to knowledge graphs consisting of entities and
relationships to preserve the structure that's inherent in the sources.

### How does Graph RAG work?

Just like with standard RAG, the very first step is ingestion. Here, knowledge sources are processed and
split into entities and relationships that are stored in a graph database. This can either be done manually
or automatically using an LLM.

After this initial step, upon receiving a query, the goal is to retrieve the information that is most
relevant to the query from the graph database. This can be done by querying the graph database to
extract relevant nodes and/or sub-graphs. As an example, let's consider the case where we have a graph
database that consists of entities and relationships that have been derived from bug reports. If the
query is "NullPointerException when invoking method `foo`", we can query the graph database to find
bug reports with similar "Descriptions" and then extract additional relevant information from these bug
reports like the "Resolution" for example.

The retrieved information is then included in a prompt to the LLM along with the original query. This
helps the LLM to generate a response that is grounded in the retrieved information.

### Graph RAG with Embedding-Based Retrieval

In addition to simply querying the graph database, it's also possible to create a vector representation
(embedding) for each entity in the graph and then use embedding-based retrieval as in standard RAG
to retrieve sub-graphs from the graph database that are most similar to the query.

### Our implementation

Wise Agents provides a `wiseagents.agents.GraphRAGWiseAgent` that you can use or extend to answer
questions using Graph RAG with embedding-based retrieval.

#### Graph Database Integration

A `GraphRAGWiseAgent` makes use of a `wiseagents.graphdb.WiseAgentGraphDB`, which provides integration
with a graph database. Wise Agents provides an implementation of this abstract class that makes use
of `Neo4j`, see `wiseagents.graphdb.Neo4jLangChainWiseAgentGraphDB`. An advantage of using Neo4j
for the graph database integration is that it's possible to make use of embedding-based retrieval very
easily. We are planning on adding integration with additional graph databases in the future. You can
also create your own implementations depending on the graph database you'd like to use.

A `GraphRAGWiseAgent` makes use of a `wiseagents.graphdb.WiseAgentGraphDB`. 

## What are Hallucinations?

Although retrieval augmented generation (RAG) and graph-based retrieval augmented generation (Graph RAG)
are meant to ground LLM responses using retrieved information, it's still possible for the LLM
to "hallucinate", i.e., generate responses that are not factually correct.

To address this, Wise Agents also provides agent implementations that can be used to challenge
the response that's been obtained from an LLM using the Chain-of-Verification (CoVe) method to
try to prevent hallucinations. For detailed information about the CoVe method, check out this
[paper](https://arxiv.org/pdf/2309.11495). We'll also describe the CoVe method below.

### How does Chain-of-Verification (CoVe) work?

Chain-of-Verification (CoVe) is a method that involves verifying the baseline response generated by
an LLM by planning verification questions to try to fact-check the baseline response. These verification
questions are answered independently to avoid biases from the other answers and then a final revised
response is determined using the baseline response together with the verification results that might have
found inconsistencies. The CoVe method helps to decrease hallucinations.

### Our implementation

Wise Agents provides a `wiseagents.agents.CoVeChallengerRAGWiseAgent` that you can use or extend to
challenge responses for RAG obtained from an LLM using the CoVe method.

Wise Agents also provides a `wiseagents.agents.CoVeChallengerGraphRAGWiseAgent` that you can use or
extend to challenge responses for Graph RAG obtained from an LLM using the CoVe method.