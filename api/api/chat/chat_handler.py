import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from api.search.search_handler import SearchHandler
import json
from types import SimpleNamespace

search_handler = SearchHandler()


class ChatHandler:
    def __init__(self) -> None:
        self.llm = AzureChatOpenAI(
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
        )

    def get_chat_response(self, input_text):

        greetings = ["hi", "hello", "hey", "hiya", "good morning", "good afternoon"]
        thanks = ["thanks", "thank you", "cheers", "nice one", "much appreciated"]
        goodbyes = ["bye", "goodbye", "see you", "see ya"]

        input_lower = input_text.strip().lower()

        if any(greet in input_lower for greet in greetings):
            return SimpleNamespace(content="Hi there! How can I help you today with your bin collections?")

        if any(thank in input_lower for thank in thanks):
            return SimpleNamespace(content="No problem, if you have any more questions let me know!")
        
        if any(bye in input_lower for bye in goodbyes):
            return SimpleNamespace(content="Goodbye! Thanks for your time.")



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
