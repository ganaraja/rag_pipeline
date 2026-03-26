Create a Python full stack application for a RAG with frontend and Backend details as follows.

frontend-

The frontend is based on react framework. Use best practices wherever possible. It has two tabs

1.  Admin Tab
    The Admin Tab consists of a pane which has two options
    1.  Collection
        The Collection has a dropdown combo box which displays a set of collections in the Qdrant VectorDB.
        If there are no collections, it should display None otherwise show the default one
        It needs to have two buttons
        Create Button - It is used to create new collections in VectorDB.
        On clicking this, one should be given an option to input the name of the Collection.
        Trying to create collection with Empty input textbox and other erroneous cases needs to be handled
        The Input textbox should be visible only on clicking Create Button

                Delete Button - It is used to delete collections in VectorDB.
                     On clicking this, the collection in the Combo box presently displayedd should be deleted with a caution like
                     for eg. "Are you sure you want to delete the collection ?"
                     Trying to delete collection with Empty Combo and other erroneous cases needs to be handled

            File Operations:

                The user should be able to specify the filename and upload to the vectorDB Using the following process
                    It should call the Upload api to the backend to upload the file received.

2.  User Tab
    The Useer Tab is an chat interface just like https://layla.ai
    User should be able to question and get answers suitable from the LLM

Use a blend of Amazon.com and also https://layla.ai. Use wise decision to improve the look and feel

Frontend Testing:
Jest as test runner, React Testing Library (RTL) for component and interaction tests (npm run test in src/frontend).
On every code change: add/update tests and run full test suite; fix until all pass.

Backend:

    Create a set of FastAPI to support the frontend
    Upload Api:
        This is to be strictly used by the Admin tab.
        The Upload API should be able to receive the file and should do all the processing as below
            1. Creating a python Class for implementing the ChunkingStrategy with all the steps outlined in the file at this path /Users/ganaraja/repos/rag/lab2/chunking_lab/chunking_pipeline/docs/notebooks/03-chunking_pipeline.ipynb
            2. Create classes for each models -
                    1. **Matryoshka Embeddings** - For efficient initial retrieval with truncated dimensions
                    2. **ColBERT Embeddings** - For detailed semantic matching with late interaction
                    3. **SPLADE Embeddings** - For sparse lexical retrieval with term expansion
                    4. **Cross-Encoder Reranking** - For final precision ranking
                    Obtain various models embedddings as per this sample file. /Users/ganaraja/repos/rag/lab3/retrieval_pipeline/docs/notebooks/04-combined_pipeline.ipynb
            3. Create a class for interacting with QdrantDB and it performs all the operations outlined in this file /Users/ganaraja/repos/rag/lab3/retrieval_pipeline/docs/notebooks/04-combined_pipeline.ipynb.

            4. Create two class MultiEmbeddingRetrievalPipeline with prefetch and MultiEmbeddingRetrievalPipelineMultiEmbeddingRetrievalPipeline without prefectch. The sample is outline in this file - /Users/ganaraja/repos/rag/lab3/retrieval_pipeline/docs/notebooks/04-combined_pipeline.ipynb.

            5. Once the the fileupload is successful/failure, indicate to the frontend.
    User Interaction Api:
        Whenever a User sends in a query, The query is sent to the Qdrant class which searches the collection created by the Admin. Once the results are fetched, it is passed to the LLM chosen at the Ollama Inference server to formulate a good answer to the user
        Create Classes wherever required - Use the example code - /Users/ganaraja/repos/rag/lab3/retrieval_pipeline/docs/notebooks/04-combined_pipeline.ipynb.

There are other helpful code if required - feel free to use /Users/ganaraja/repos/rag/

Backend Testing:
Create pytest unit, integration cases the above backend classes
pytest; test classes and interactions in tests/ (run with PYTHONPATH=src pytest tests/ after uv sync or pip install -e ".[dev]").

Dependency Management
Use uv instead of pip for Python.
