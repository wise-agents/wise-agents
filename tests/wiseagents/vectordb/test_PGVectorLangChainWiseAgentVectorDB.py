import os

from wiseagents.vectordb import Document, PGVectorLangChainWiseAgentVectorDB


def get_connection_string():
    return f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@localhost:6024/{os.environ['POSTGRES_DB']}"


def set_env(monkeypatch):
    """
        This test requires a running pgvector instance. The required
        vector database can be started using the run_vectordb.sh script.
    """
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    monkeypatch.setenv("POSTGRES_DB", "postgres")


def test_create_and_delete_collection(monkeypatch):
    set_env(monkeypatch)
    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())
    pg_vector_db.get_or_create_collection("test_collection")
    assert "test_collection" in pg_vector_db._vector_dbs
    pg_vector_db.delete_collection("test_collection")
    assert "test_collection" not in pg_vector_db._vector_dbs


def test_insert_documents_and_query(monkeypatch):
    set_env(monkeypatch)
    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())

    try:
        # should be no matches initially
        documents = pg_vector_db.query(["tall building"], "test_collection", 1)
        assert len(documents[0]) == 0

        pg_vector_db.insert_documents([Document(id="1", content="The CN Tower is located in Toronto.")],
                                      "test_collection")
        documents = pg_vector_db.query(["tall building"], "test_collection", 1)
        assert "CN Tower" in documents[0][0].content

        pg_vector_db.insert_documents([Document(content="Toronto is a city in the province of Ontario.",
                                                metadata={"source": "cities.com"}),
                                       Document(content="There are maple trees in Canada.",
                                                metadata={"source": "countries.com"}),
                                       Document(content="The beaver is a national symbol of Canada",
                                                metadata={"source": "symbols.com"})
                                       ],
                                      "test_collection")

        documents = pg_vector_db.query(["animal"], "test_collection")
        assert "beaver" in documents[0][0].content
        # Default value for top k is 4
        assert len(documents[0]) == 4

        documents = pg_vector_db.query(["plant", "region"], "test_collection", 1)
        assert "maple trees" in documents[0][0].content
        assert "province" in documents[1][0].content
    finally:
        pg_vector_db.delete_collection("test_collection")


def test_insert_or_update_documents_and_query(monkeypatch):
    set_env(monkeypatch)
    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())

    try:
        # should be no matches initially
        documents = pg_vector_db.query(["landmark"], "test_collection", 1)
        assert len(documents[0]) == 0

        pg_vector_db.insert_or_update_documents([Document(id="2", content="The Eiffel Tower is located in France.")],
                                                "test_collection")
        documents = pg_vector_db.query(["landmark"], "test_collection", 1)
        assert "Eiffel Tower" in documents[0][0].content

        pg_vector_db.insert_or_update_documents([Document(id="2", content="The Louvre museum is located in France",
                                                          metadata={"source": "cities.com"})], "test_collection")
        documents = pg_vector_db.query(["landmark"], "test_collection")
        assert "Louvre museum" in documents[0][0].content

        documents = pg_vector_db.query(["Eiffel Tower"], "test_collection", 4)
        for documents_list in documents:
            for document in documents_list:
                assert "Eiffel Tower" not in document.content
    finally:
        pg_vector_db.delete_collection("test_collection")


def test_delete_documents(monkeypatch):
    set_env(monkeypatch)
    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())

    try:
        pg_vector_db.insert_documents([Document(id="123", content="Tower Bridge is located in London."),
                                       Document(id="456", content="The CN Tower is located in Toronto."),
                                       Document(id="789", content="London is in the UK.")],
                                      "test_collection")
        documents = pg_vector_db.query(["tower"], "test_collection", 2)
        assert "Tower Bridge" in documents[0][0].content
        assert "CN Tower" in documents[0][1].content

        pg_vector_db.delete_documents(["456"], "test_collection")
        documents = pg_vector_db.query(["tower"], "test_collection", 2)
        assert "Tower Bridge" in documents[0][0].content
        assert "CN Tower" not in documents[0][1].content
    finally:
        pg_vector_db.delete_collection("test_collection")
