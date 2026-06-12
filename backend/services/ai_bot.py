# import logging
# from typing import List
# from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
# from langchain_openai import ChatOpenAI
# from ..config import settings
# from ..models import Message
# from .rag_service import search_knowledge_base
# import json, re

# logger = logging.getLogger(__name__)

# class AIChatBot:
#     def __init__(self):
#         if settings.llm_api_key:
#             self.llm = ChatOpenAI(
#                 base_url=settings.llm_api_url,
#                 api_key=settings.llm_api_key,
#                 model=str(settings.llm_model),
#                 temperature=0.7)
        
#         self.default_system_prompt = "You are a helpful AI assistant. Respond in Vietnamese concisely and professionally."

#     def _build_message_chain(self, system_prompt_content: str, past_messages: List[Message], new_content: str) -> list:
#         """
#         Constructs the message chain for the LLM, including the system prompt,
#         chat history, and the latest user query.
#         """
#         messages: List[BaseMessage] = [SystemMessage(content=system_prompt_content)]
        
#         # Append historical messages
#         for msg in past_messages:
#             role = str(msg.role)
#             content = str(msg.content)
#             if role == "user":
#                 messages.append(HumanMessage(content=content))
#             else:
#                 messages.append(AIMessage(content=content))
                
#         # Append the latest user query
#         messages.append(HumanMessage(content=new_content))
        
#         return messages

#     def get_response(self, past_messages: List[Message], new_content: str, conv_id: int, has_attachments: bool) -> str:
#         """
#         Generates an AI response, utilizing RAG context if attachments exist in the conversation.
#         """
#         rag_context = ""
#         system_prompt = self.default_system_prompt

        
#         # Retrieve context from Milvus if attachments are present
#         if has_attachments:
#             try:
#                 rag_context = search_knowledge_base(new_content, conv_id)
#             except Exception as e:
#                 logger.error(f"Failed to retrieve RAG context: {e}")

#         # Dynamically adjust the system prompt if RAG context is found
#         if rag_context:
#             system_prompt = f"""You are a professional AI Docter assistant.
#             Based on the EXTRACTED DOCUMENTS below, answer the user's question.
#         - Always cite the source using [Page X] if you extract information from the documents.
#         - If the information is not present in the documents, state honestly: "The provided documents do not mention this information." Do not fabricate data.

#         --- EXTRACTED DOCUMENTS ---
#         {rag_context}
#         ---------------------------
#         """
#         # Không nên thêm Past Messages vào thằng invoke
#         messages = self._build_message_chain(system_prompt, past_messages, new_content)

#         try:
#             logger.info("Invoking Azure OpenAI model...")
#             response = self.llm.invoke(messages)
#             return str(response.content)
#         except Exception as e:
#             logger.error(f"Azure OpenAI invocation failed: {str(e)}")
#             raise Exception(f"AI Model connection error: {str(e)}")

import logging
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from ..config import settings
from ..models import Message
from .rag_service import search_knowledge_base

logger = logging.getLogger(__name__)

class AIChatBot:
    def __init__(self):
        if not settings.llm_api_key:
            logger.error("LLM API Key is missing!")
            raise ValueError("LLM API Key must be provided in settings.")

        # LLM dành cho việc Routing/Check Logic (Cần tính chính xác tuyệt đối, temp = 0.0)
        self.router_llm = ChatOpenAI(
            base_url=settings.llm_api_url,
            api_key=settings.llm_api_key,
            model=str(settings.llm_model),
            temperature=0.0 
        )

        # LLM dành cho việc trả lời người dùng (Cần bám sát context, ít sáng tạo, temp = 0.1)
        self.answer_llm = ChatOpenAI(
            base_url=settings.llm_api_url,
            api_key=settings.llm_api_key,
            model=str(settings.llm_model),
            temperature=0.4
        )
        
        self.default_system_prompt = "You are a helpful AI assistant. Respond in English professionally and more detail."

    def _build_message_chain(self, system_prompt_content: str, past_messages: List[Message], new_content: str) -> List[BaseMessage]:
        """
        Constructs the message chain for the LLM, including the system prompt, chat history, and latest query.
        """
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt_content)]
        
        for msg in past_messages:
            if str(msg.role) == "user":
                messages.append(HumanMessage(content=str(msg.content)))
            else:
                messages.append(AIMessage(content=str(msg.content)))
                
        messages.append(HumanMessage(content=new_content))
        return messages

    def get_response(self, past_messages: List[Message], new_content: str, conv_id: int, has_attachments: bool) -> str:
        """
        Generates an AI response, utilizing a Router LLM to decide if RAG is needed.
        """
        rag_context = ""
        system_prompt = self.default_system_prompt
        should_search_rag = False

        # BƯỚC 1: ROUTING - Chỉ gọi AI kiểm tra nếu thực sự có file đính kèm
        if has_attachments:
            system_prompt_ai_checker = """
            You are a RAG router. Decide if the user's question requires searching the user's uploaded documents.
            Output ONLY STRING: 'rag_search' or 'no_search'.

            Rules:
            - Output 'rag_search' if the question depends on uploaded documents, needs exact details, or citations.
            - Output 'no_search' if it is a general greeting, casual question, or can be answered without documents.
            """
            
            message_check = [
                SystemMessage(content=system_prompt_ai_checker),
                HumanMessage(content=new_content)
            ]

            try:
                # Dùng router_llm (temp=0.0) để đảm bảo output luôn chuẩn format
                rag_check_response = self.router_llm.invoke(message_check)
                # Parse nội dung (extract string từ AIMessage)
                router_decision = str(rag_check_response.content).strip().lower()
                
                if router_decision == "rag_search":
                    should_search_rag = True
                    logger.info("Router decided to perform RAG search.")
                else:
                    logger.info("Router decided RAG is NOT needed.")
            except Exception as e:
                logger.error(f"Router LLM failed: {e}. Defaulting to no_search.")

        # BƯỚC 2: RETRIEVAL - Lấy Context nếu Router quyết định là cần thiết
        if should_search_rag:
            try:
                rag_context = search_knowledge_base(new_content, conv_id)
            except Exception as e:
                logger.error(f"Failed to retrieve RAG context: {e}")

        # BƯỚC 3: PROMPT ENGINEERING - Điều chỉnh prompt nếu có RAG
        if rag_context:
            system_prompt = f"""You are a professional AI Doctor assistant.
            Based on the EXTRACTED DOCUMENTS below, answer the user's question in English.
            
            Rules:
            - If you use ANY information from the provided context/documents, you MUST cite it inline.
            - A citation MUST include both Source and Page in this exact format: (Page <page> from <source>)
            - Place the citation immediately after the sentence/claim it supports.
            - If multiple sentences use the same evidence, cite at least once per paragraph or after the last related sentence.
            - If the answer is not supported by the context, say you don't have enough information and do not invent.
            - If the information is not present in the documents, state honestly: "The provided documents do not mention this information." Do not fabricate data.

            --- EXTRACTED DOCUMENTS ---
            {rag_context}
            ---------------------------
            """

        # BƯỚC 4: GENERATION - Lắp ráp tin nhắn và gọi LLM
        messages = self._build_message_chain(system_prompt, past_messages, new_content)

        try:
            logger.info("Invoking Azure OpenAI model for final answer...")
            # Dùng answer_llm (temp=0.1)
            response = self.answer_llm.invoke(messages)
            return str(response.content)
        except Exception as e:
            logger.error(f"Azure OpenAI invocation failed: {str(e)}")
            raise Exception(f"AI Model connection error: {str(e)}")