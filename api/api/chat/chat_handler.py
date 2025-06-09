import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from api.search.search_handler import SearchHandler
from api.enrich.audit_processor import AuditProcessor

search_handler = SearchHandler()
audit_processor = AuditProcessor()

class ChatHandler:
    def __init__(self) -> None:
        self.llm = AzureChatOpenAI(
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
        )

    def get_chat_response(self, input_text):

        search_response = search_handler.get_query_response(input_text)
        audit_text = audit_processor.get_audit_text()
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a helpful assistant to The London Fire Brigade that is responsible for reviewing uploaded audit documents. An audit document is a review of fire safety compliance according to the Regulatory Reform (Fire Safety) Order 2005. Your task is to read the audit and advise on the following: 
                    - Are any key items missing from the audit? 
                    - Are certain audit comments documented under the incorrect section according to the RRO 2005?
                    - Is the language used in the audit clear and well written english? 
                    - Are there any comments that are ephemeral or not relevant to the audit?
                    - Are there any other issues with the audit that would require the attention of a manager or senior auditor? 
                    """,
                ),
                (
                    "human", 
                    """{input}. 
                    This is the information from the audit: {audit_text}.

                    Respond using only information from the following sources: 
                    - Information from the Regulatory Reform Order 2005, which is available online
                    - The relevant internal documentaion and guidelines: {information}
                    """),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke(
            {
                "input": input_text,
                "information": search_response,
                "audit_text": audit_text
            }
        )

        return response
