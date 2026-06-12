# '''
#     Semantic Search: Use dense vector: ideal for unstructured data such as text, images, and audio.
#     Full-text Search: complementing semantic search with keyword matching, ideal for structured data and specific keyword queries.
#     Metadata filtering: On top of vector search, applying constraints like date ranges, categories, or tags to narrow down results.
# '''
# from .config import settings
# from pymilvus import Function, FunctionType, MilvusClient, DataType
# from pytz import timezone





# def init_milvus(uri: str = f'milvus:// {settings.milvus_host}:{settings.milvus_port}', db_name: str = 'knowledge_base') -> MilvusClient:
    
#     client = MilvusClient(uri=uri)

    
#     if db_name not in client.list_databases():
#         client.create_database(db_name=db_name)

#     schema = client.create_schema(
#         auto_id=False,
#         enable_dynamic_field=False
#         )
    
#     schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
#     schema.add_field(field_name='conservation_ids', datatype=DataType.INT32, is_primary=False, nullable=False, auto_id=False)
#     schema.add_field(field_name='content', datatype=DataType.VARCHAR, max_length=65535, nullable=False)
#     schema.add_field(field_name='embeddings', datatype=DataType.FLOAT_VECTOR, dim=1024, nullable=False)   # Depend on embedding model, we can change the dimension in the future
#     schema.add_field(field_name='sources', datatype=DataType.VARCHAR, max_length=255, nullable=True, is_primary=False)
#     schema.add_field(field_name='pages', datatype=DataType.INT32, nullable=True, is_primary=False)
#     schema.add_field(field_name='file_ids', datatype=DataType.INT64, nullable=True, is_primary=False)

#     index_params = client.prepare_index_params()

#     index_params.add_index(
#         field_name = "embedding",
#         index_type = "HNSW",
#         metric_type = "COSINE",
#         params = {
#             "M": 16,  
#             "efConstruction": 200, 
#             "efSearch": 50  
#         }
#     )

#     text_embedding_function = Function(
#         name="openai_embedding_function",
#         function_type=FunctionType.TEXTEMBEDDING,
#         input_field_names=["content"],  
#         output_field_names=["embeddings"],
#         params={
#             "provider": "azure",
#             "api_key": settings.embed_api_key,
#             "api_url": settings.embed_api_url,
#             "model_name": settings.embed_model,
#             "dim": settings.dimension
#         }
#     )
#     schema.add_function(text_embedding_function)

#     if not client.has_collection(collection_name='knowledge_base'):
        
#         client.create_collection(
#             collection_name=str(settings.collection_name),
#             schema=schema,
#             index_params=index_params,
#             num_shards=1,
#             properties={
#                 "collection.ttl.seconds": 7200,
#                 "timezone": timezone('UTC')
#             },
#             consistent_level="Bound" 
#         )
#     client.create_alias(
#         collection_name='knowledge_base',
#         alias='user_doc'
#     )

#     client.load_collection(collection_name="knowledge_base",
#                            skip_load_dynamic_field=True)
    
#     return client
    

# if __name__ == "__main__":
#     client = init_milvus()


from json import load

from .config import settings
from pymilvus import Function, FunctionType, MilvusClient, DataType
import logging

logger = logging.getLogger(__name__)

def init_milvus(db_name: str = 'rag_database') -> MilvusClient:
    
    uri = f"http://{settings.milvus_host}:{settings.milvus_port}"
    client = MilvusClient(uri=uri)


    if db_name not in client.list_databases():
        logger.info(f"Creating database: {db_name}")
        client.create_database(db_name=db_name)
    

    client.use_database(db_name)

    collection_name = str(settings.collection_name)

    
    if client.has_collection(collection_name=collection_name):
        logger.info(f"Collection '{collection_name}'exists. Loading into RAM...")
        client.load_collection(collection_name=collection_name)
        return client

    logger.info(f" Create Collection '{collection_name}' with Auto-Embedding...")

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    
    schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, auto_id=True)
    schema.add_field(field_name="conversation_id", datatype=DataType.INT64, nullable=False) 
    schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=65535, nullable=False)
    schema.add_field(field_name="embeddings", datatype=DataType.FLOAT_VECTOR, dim=settings.dimension, nullable=False)
    schema.add_field(field_name="sources", datatype=DataType.VARCHAR, max_length=255, nullable=True)
    schema.add_field(field_name="pages", datatype=DataType.INT32, nullable=True)
    schema.add_field(field_name="file_id", datatype=DataType.INT64, nullable=True)

    
    # text_embedding_function = Function(
    #     name="azopenai",
    #     function_type=FunctionType.TEXTEMBEDDING,
    #     input_field_names=["content"],  
    #     output_field_names=["embeddings"], 
    #     params={
    #         "provider": "azure_openai", 
    #         "model_name": "text-embedding-3-small",  
    #         # "dim": settings.dimension
    #     }
    # )
    # schema.add_function(text_embedding_function)

   
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embeddings", 
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 200, "efSearch": 50}
    )

    
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
        index_params=index_params,
        num_shards=1,
        consistent_level="Bounded" 
    )

    
    aliases = client.list_aliases(collection_name=collection_name)
    if 'user_doc' not in aliases:
        client.create_alias(collection_name=collection_name, alias='user_doc')

    
    client.load_collection(collection_name=collection_name, skip_load_dynamic_field=True)
    logger.info("Done Milvus and collection setup.")
    
    return client



# if __name__ == "__main__":
#     client = init_milvus()

    


        


# client = MilvusClient(uri='milvus://localhost:19530')

# # Create a new database named 'knowledge_base'
# client.create_database(
#     db_name='knowledge_base',
# )

# Create schema for the collection

# schema = client.create_schema(
#     auto_id=False,
#     enable_dynamic_field=False,
# )


# '''
#     We can add source and page(located in the document) as metadata fields in the future, but for now, we will only focus on the three fields mentioned above.
#     Example of metadata fields:
#     source_field = FieldSchema(name='source', data_type=DataType.VARCHAR, max_length=255, nullable=True, is_primary=False)
#     page_field = FieldSchema(name='page', data_type=DataType.INT32, nullable=True, is_primary=False)

# '''


# # Create a schema for the 'user_document' collection with fields 'conservation_id', 'content', and 'embedding'
# schema.add_field(field_name='conservation_id', data_type=DataType.INT32, is_primary=True, nullable=False, auto_id=False)
# schema.add_field(field_name='content', data_type=DataType.VARCHAR, max_length=65535, nullable=False)
# schema.add_field(field_name='embedding', data_type=DataType.FLOAT_VECTOR, dim=1024, nullable=False)   # Depend on embedding model, we can change the dimension in the future


# # Prepare index parameters for the 'embedding' field

# index_params = client.prepare_index_params()


# '''
#     với index_params = {}



# '''



# index_params.add_index(
#     field_name = "embedding",
#     index_type = "HNSW",
#     metric_type = "COSINE",
#     'params': {
#         "M": 16,  # Number of neighbors to consider for each node in the HNSW graph. A higher M can improve recall but may increase index size and search time.
#         "efConstruction": 200,  # Controls the trade-off between index construction time and search performance. A higher efConstruction can improve recall but will increase index construction time.
#         "efSearch": 50  # Controls the trade-off between search speed and recall. A higher efSearch can improve recall but will increase search time.

#     }
# )

# # Check if the collection 'user_document' already exists in the 'knowledge_base' database, if not, create it with the defined schema and index parameters
# if not client.has_collection(collection_name='user_document'):
#     # Create a new collecytion named 'user_document' in the 'knowledge_base' database with the defined schema and index parameters
#     client.create_collection(
#         collection_name='user_document',
#         schema=schema,
#         index_params=index_params,
#         num_shards=1,
#         properties={
#             "collection.ttl.seconds": 7200,   # SET TTL for 2 hours (7200 seconds), after which the data will be automatically deleted
#             "timezone": timezone('UTC')
#         },
#         consistent_level="Bound"     # Strong consistency level for read operations, Bound ensures that read operations will see the most recent write operations, providing strong consistency.
#     )

# client.create_alias(
#     collection_name='user_document',
#     alias='user_doc'
# )


# # sample_data



# # Before searching, we need to insert some data into the collection. Here is an example of how to insert data into the 'user_document' collection:



# data = [
#     {
#         "conservation_id": 1,
#         "content": "What is the capital of France?",
#         "embedding": [0.1, 0.2, 0.3]  # Replace with actual embedding
#     }
# ]



# # RAG WORKFLOW:
# # 1. User query -> embedding -> search in vector database -> retrieve relevant documents -> generate answer based on retrieved documents and user query -> return answer to user

# # Assumption: We have already chunk from PDF Loaders

# # Step1: PDF Loader -> Text Splitter -> Embedding Model -> Vector Database (Milvus)

# # sources = [chunk.metadata['source'] for chunk in chunks]
# # pages = [chunk.metadata['page'] for chunk in chunks]
# # page_content = [chunk.page_content for chunk in chunks]
# # content_embeddings = [embedding.encode(chunk) for chunk in chunks]

# # collection = client.get_collection(collection_name="user_document")
# # collection.insert([sources, pages, page_content, content_embeddings])




# # INSERT DATA in user_document collection
# client.insert(
#     collection_name="user_document",
#     data=data
# )


# # 

# # Query with filtering and vector search

# # db.using_database('knowledge_base')
# # collection = client.get_collection(collection_name="user_document") 
# # collection.load()  # Load the collection into memory before performing search operations



# # Embedding for the user query
# # user_query = "What is the capital of France?"

# def search_milvus(user_query, collection, limit=5):
#     # Perform a vector search with filtering on the 'user_document' collection
#     query_embedding = embedding.encode(user_query)  # Replace with actual embedding generation for the user query

#     search_paramas = {
#         "index_type": "HNSW",
#         "metric_type": "COSINE",
#         "params": {
#             'M': 16,  # Number of neighbors to consider for each node in the HNSW graph. A higher M can improve recall but may increase index size and search time.
#             'efConstruction': 200,  # Controls the trade-off between index construction time and search performance. A higher efConstruction can improve recall but will increase index construction time.
#             "efSearch": 50  # Controls the trade-off between search speed and recall. A higher efSearch can improve recall but will increase search time.
#         }

#     }
#     results = collection.search(
#         data=[query_embedding],
#         anns_field="embedding",   # The name of the field in the collection that contains the vector embeddings to be searched against.
#         param=search_paramas,
#         limit=limit,
#         output_fields=["content", 'page' "embedding"]
#     )
#     return results
    
# filter = 'conservation_id == 1'
# results = client.query(
#     collection_name="user_document",
#     filter=filter,
#     output_fields=["content", "embedding"]
# )


# # results = search_milvus(user_query, collection, 4)
# def filter_results(results):
#     data = {}
#     distances = []
#     page_numbers = []
#     contents = []
#     sources = []

#     for result in results[0]:  # Assuming results is a list of lists, we take the first list of results
#         distances.append(result.distance)
#         page_numbers.append(result.entity.get('page'))
#         contents.append(result.entity.get('content'))
#         sources.append(result.entity.get('source'))

#     data['content'] = contents
#     data['distance'] = distances
#     data['page'] = page_numbers
#     data['source'] = sources

#     return data



# Define embedding function for the user query

# text_embedding_function = Function(
#     name="openai_embeddign_function",
#     function_type=FunctionType.TEXTEMBEDDING,
#     input_field_names=["content"],  # The name of the field in the collection that contains the text data to be embedded.
#     output_field_names=["dense"],
#     params={
#         "provider": "azure",
#         "api_key": settings.EMBED_API_KEY,
#         "api_url": settings.EMBED_API_URL,
#         "model_name": settings.EMBED_MODEL,
#     }
#     dim=1536
# )

# schema.add_function(text_embedding_function)












