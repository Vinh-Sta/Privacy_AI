import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pymilvus import MilvusClient
from ..config import settings
import logging
from ..database import SessionLocal  
from .. import models
from ..config import settings
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

embedder = OpenAIEmbeddings(
    base_url=settings.embed_api_url,
    api_key=settings.embed_api_key,
    model=str(settings.embed_model),
    dimensions=settings.dimension
)
from pathlib import Path
import re

def clean_source(source: str) -> str:
    name = Path(source).name  # 1775788669_Prostate-Cancer-Review-...pdf
    # bỏ prefix dạng số + "_" ở đầu tên file
    name = re.sub(r"^\d+_", "", name)
    return name

def get_milvus_client():
    return MilvusClient(uri=f"http://{settings.milvus_host}:{settings.milvus_port}")


def process_and_store_pdf(file_path: str, conversation_id: int, attachment_id: int):
    logger.info(f"Processing file: {file_path}")
    
    loader = PyPDFLoader(file_path)
    documents = loader.load()


    # Code here for summary text in pdf file
    # Summary text in pdf file 
    # full_text = "\n".join(doc.page_content for doc in documents)
    # # print(full_text[0:30])

    # system_prompt_summary = f"""You are a professional summarization assistant.

    # REQUIREMENTS:
    # - Output MUST be exactly ONE single paragraph.
    # - Do NOT use bullet points, numbering, headings, or line breaks.
    # - Do NOT include extra whitespace/new lines.
    # - Maximum length: 1000 characters (including spaces).

    # RAW TEXT:
    # {full_text}
    # """.strip()


    # query = "Summarize the RAW TEXT. Follow REQUIREMENTS strictly."

    # message_summary = [
    #     SystemMessage(content=system_prompt_summary),
    #     HumanMessage(content=query)
    # ]

    # try:
    #     llm = ChatOpenAI(
    #         base_url=settings.llm_api_url,
    #         api_key=settings.llm_api_key,
    #         model=str(settings.llm_model),
    #         temperature=0.0 
    #     )
    #     response = llm.invoke(message_summary)
    #     summary = response.content
    #     logger.info("Done summary file", len(summary))
    # except Exception as e:
    #     print(" Error happened:", e)

    # db = SessionLocal()
    # try:
    #     attachment = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
    #     if attachment:
    #         attachment.file_content = summary   # type: ignore
    #         db.commit()
    #         logger.info(f"Save summary content file:{attachment_id}")
    # finally:
    #     db.close() # Nhớ đóng DB



    ## END CODE HERE
    
    if not documents:
        logger.error("Empty PDF file or failed to load.")
        return False

    MARKDOWN_SEPARATORS = [
        "\n#{1,6} ",
        "```\n",  
        "\n\\*\\*\\*+\n",  
        "\n---+\n",  
        "\n___+\n",  
        "\n\n",  
        "\n",  
        " ",  
        "",  
    ]  
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, 
        chunk_overlap=200, 
        separators=MARKDOWN_SEPARATORS,
        add_start_index=True,
        strip_whitespace=True
    )


    chunks = text_splitter.split_documents(documents)
    logger.info(f"Had {len(chunks)} chunks after splitting the document.")

    # thêm embedding vào đây
    texts = [c.page_content for c in chunks]
    embs = embedder.embed_documents(texts)

    data_to_insert = []
    for chunk, emb in zip(chunks, embs):
        data_to_insert.append({
            "conversation_id": conversation_id,
            "content": chunk.page_content,
            "embeddings": emb,
            "sources": file_path,
            "pages": chunk.metadata.get("page", 0),
            "file_id": attachment_id
        })

    try:
        client = get_milvus_client()
        client.using_database("rag_database") 
        
        insert_result = client.insert(
            collection_name=str(settings.collection_name), 
            data=data_to_insert
        )


        # Forced silling and persistence to ensure data is available for search immediately
        client.flush(collection_name=str(settings.collection_name))

        client.load_collection(collection_name=str(settings.collection_name))
        
        logger.info(f"Done {insert_result['insert_count']} chunks into Milvus.")


        db = SessionLocal() # Mở một kết nối DB mới cho tiến trình ngầm
        try:
            attachment = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
            if attachment:
                attachment.status = "Done"   # type: ignore
                db.commit()
                logger.info(f"Đã xử lý xong file {attachment_id}")
        finally:
            db.close() # Nhớ đóng DB
            
    except Exception as e:
        logger.error(f"Lỗi khi xử lý file: {str(e)}")
        # Có thể update status thành "Failed" nếu muốn
        db = SessionLocal()
        try:
            attachment = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
            if attachment:
                attachment.status = "Failed"   # type: ignore
                db.commit()
        finally:
            db.close()


def search_knowledge_base(query: str, conversation_id: int, top_k: int = 5) -> str:
    
    try:
        logger.info(f"Searching knowledge base for query: '{query}'")

        query_vector = embedder.embed_query(query)

        client = get_milvus_client()
        client.using_database("rag_database")
        
        
        results = client.search(
            collection_name=str(settings.collection_name),
            data=[query_vector],
            limit=top_k,
            filter=f"conversation_id == {conversation_id}", 
            output_fields=["content", "pages", "sources"]
        )

        # context = ""
        # if results and len(results[0]) > 0:
        #     logger.info(f" Find {len(results[0]) } relevant chunks in Milvus.")
        #     for hit in results[0]:
        #         content = hit["entity"]["content"]
        #         page = hit["entity"].get("pages", "Unknown")
        #         source = hit["entity"].get("sources", "Unknown")
        #         context += f"[Page {page}]: {content}\n\n"
        context = ""
        if results and len(results[0]) > 0:
            logger.info(f"Find {len(results[0])} relevant chunks in Milvus.")
            for i, hit in enumerate(results[0], start=1):
                entity = hit["entity"]
                content = entity.get("content", "")
                page = entity.get("pages", "Unknown")
                source = clean_source(entity.get("sources", "Unknown"))  # ví dụ: file name / url

                context += (
                    f"[{i}] Source: {source} | Page: {page}\n"
                    f"{content}\n\n"
                )
        return context

    except Exception as e:
        logger.error(f"Error occurred while searching knowledge base: {e}")
        return ""



