import os
from IPython import embed
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from dotenv import load_dotenv
import re
from openai import base_url
load_dotenv()

llm_api_url = os.getenv("LLM_API_URL")
llm_api_key = os.getenv("LLM_API_KEY")
llm_api_version = os.getenv("LLM_API_VERSION")
llm_model = os.getenv("LLM_MODEL")


# embed_api_url = os.getenv("EMBED_API_URL")
# embed_api_key = os.getenv("EMBED_API_KEY")
# embed_model = os.getenv("EMBED_MODEL")
# dimension = os.getenv("DIMENSION")

# print(dimension)

# embedder = OpenAIEmbeddings(
#     api_key=embed_api_key,
#     model=embed_model,
#     base_url=embed_api_url,
#     dimensions=dimension
# )
# print("LLM_API_URL:", llm_api_url)
# print("LLM_API_VERSION:", llm_api_version)
# print("LLM_MODEL:", llm_model)
# print("LLM_API_KEY is set:", bool(llm_api_key), "len=", 0 if not llm_api_key else len(llm_api_key))

# file_path = "/home/vinh/projects/AI_chat/backend/uploads/1775613836_healthcare_experience_of_prostate_cancer.pdf"
file_path = "/home/vinh/projects/AI_chat/backend/uploads/1775788669_Prostate-Cancer-Review-jama_raychaudhuri_2025_.pdf"
loader = PyPDFLoader(file_path)

documents = loader.load()

# title_pdf_file = documents[0].metadata
# print(title_pdf_file["title"])

full_text = "\n".join(doc.page_content for doc in documents)
# print(full_text[0:30])

system_prompt_summary = f"""You are a professional summarization assistant.

REQUIREMENTS:
- Output MUST be exactly ONE single paragraph.
- Do NOT use bullet points, numbering, headings, or line breaks.
- Do NOT include extra whitespace/new lines.
- Maximum length: 1000 characters (including spaces).

RAW TEXT:
{full_text}
""".strip()


query = "Summarize the RAW TEXT. Follow REQUIREMENTS strictly."

message_summary = [
    SystemMessage(content=system_prompt_summary),
    HumanMessage(content=query)
]


try:
    llm = ChatOpenAI(
                api_key=llm_api_key,
                model=llm_model,
                base_url=llm_api_url,
                temperature=0)
    

    response = llm.invoke(message_summary)
    summary = response.content
    # summary = re.sub(r"\s+", " ", summary).strip()

    print("Azure Chat response:", summary)
except Exception as e:
    print(" Error happened:", e)







