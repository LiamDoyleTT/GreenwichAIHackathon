import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from api.search.search_handler import SearchHandler
import json

search_handler = SearchHandler()


class ChatHandler:
    def __init__(self) -> None:
        self.llm = AzureChatOpenAI(
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
        )

    def get_chat_response(self, input_text):

        search_response = search_handler.get_query_response(input_text)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a helpful assistant that is responsible for addressing queries about bin collections.             
                    """,
                ),
                ("human", "{input}. Respond using only the information in the following bin collection rules: {information}"),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke(
            {
                "input": input_text,
                "information": search_response
            }
        )

        return response
