# wise-agents RAG architecture

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

## Our architecture and implementations

TODO

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

## How does Graph RAG work?

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

## Our architecture and implementations

TODO