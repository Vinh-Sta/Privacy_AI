from PIL.Image import radial_gradient
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pprint import pprint
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from referencing import retrieval
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from rich import ansi

load_dotenv()

loader = DirectoryLoader(
    "./papers", 
    glob="**/*.pdf", 
    show_progress=True, 
    loader_cls=UnstructuredFileLoader, 
    use_multithreading=True
)

docs = loader.load()
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
    add_start_index=True, 
    strip_whitespace=True,
    separators=MARKDOWN_SEPARATORS
)

splits = text_splitter.split_documents(docs)

embedding = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1024)



vectorstore = FAISS.from_documents(
    documents=splits,
    embedding=embedding,
    distance_strategy=DistanceStrategy.COSINE

)

retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 5, "score_threshold": 0.5}
)

template = (
    "You are a strict, citation-focused assistant for a private knowledge base.\n"
    "RULES:\n"
    "1) Use ONLY the provided context to answer.\n"
    "2) If the answer is not clearly contained in the context, say: "
    "\"I don't know based on the provided documents.\"\n"
    "3) Do NOT use outside knowledge, guessing, or web information.\n"
    "4) If applicable, cite sources as (source:page) using the metadata.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}"
)

prompt = ChatPromptTemplate.from_template(template)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

radial_chain = (
                {"content": retriever, "question": RunnablePassthrough()
                 | prompt
                 | llm
                 | StrOutputParser()},
                )

question = input("Ask a question: ")

answer = radial_chain.invoke(question)

print(answer)