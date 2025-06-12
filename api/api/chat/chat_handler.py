import os
import requests

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
    
    def trigger_api_post_request(self,url, payload):
        headers = {
            "api-key": os.environ["AZURE_RBG_ADDRESS_KEY"],
            "Ocp-Apim-Subscription-Key": os.environ["AZURE_RBG_APIM_WS_KEY"],
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an error for bad responses (4xx/5xx)
        return response.json()
    
    def trigger_api_get_request(self,url):
        headers = {
            "Ocp-Apim-Subscription-Key": os.environ["AZURE_RBG_APIM_WS_KEY"],
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an error for bad responses (4xx/5xx)
        return response.json()
    
    def parse_conversation(self, conversation_str):
        messages = []
        lines = conversation_str.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            if line.startswith('User: '):
                # Extract user message (may span multiple lines)
                user_content = line[6:]  # Remove "User: " prefix
                i += 1
                while i < len(lines) and not (lines[i].startswith('User: ') or lines[i].startswith('Assistant: ')):
                    user_content += '\n' + lines[i]
                    i += 1
                messages.append(("human", user_content.strip()))
            elif line.startswith('Assistant: '):
                # Extract assistant message (may span multiple lines)
                ai_content = line[11:]  # Remove "Assistant: " prefix
                i += 1
                while i < len(lines) and not (lines[i].startswith('User: ') or lines[i].startswith('Assistant: ')):
                    ai_content += '\n' + lines[i]
                    i += 1
                messages.append(("ai", ai_content.strip()))
            else:
                i += 1
        
        return messages

    def get_chat_response(self, input_text):

        # greetings = ["hi", "hello", "hey", "hiya", "good morning", "good afternoon"]
        # thanks = ["thanks", "thank you", "cheers", "nice one", "much appreciated"]
        # goodbyes = ["bye", "goodbye", "see you", "see ya"]

        # input_lower = input_text.strip().lower()

        # if any(greet in input_lower for greet in greetings):
        #     return SimpleNamespace(content="Hi there! How can I help you today with your bin collections?")

        # if any(thank in input_lower for thank in thanks):
        #     return SimpleNamespace(content="No problem, if you have any more questions let me know!")
        
        # if any(bye in input_lower for bye in goodbyes):
        #     return SimpleNamespace(content="Goodbye! Thanks for your time.")

        messages = self.parse_conversation(input_text)
        search_response = search_handler.get_query_response(input_text)
        
        # bot for extracting the postcode
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Your purpose is extracting the customer postcode from previous messages in a customer service conversation with a user.
                    The postcode format should be between 5 and 7 characters long and contain a space. e.g. "AB12 3CD".
                    There are only two ways that you can respond. Do not respond with anything else except the following:
                    1. If you cannot find a postcode in the conversation, respond with exactly the following phrase "No postcode found"
                    2. If you can find a postcode in the conversation history, respond with the postcode only and nothing else.
                    """), 
                    ("human", "Extract the postcode from the conversation history following. If you cannot find a postcode, respond with 'No postcode found'. Conversation history: {input}")
            ]
        )
        chain = prompt | self.llm
        postcode_response = chain.invoke(
            {
                "input": str(messages)          }
        )

        # agent for pulling out the full postcode if not yet provided
        if postcode_response.content == "No postcode found":
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an experienced and efficient customer service agent; you are answering calls to customers about missed bin collections on behalf of the Royal Borough of Greenwich.  
                        Your only role is deciding if the query is a missed bin query and if it is, then you need to ask questions first to identify what colour bin was missed and only once this is established, then asking for the customers' full postcode e.g. AB12 3CD.
                        You do not deal with missed communal bin collection or missing bins. If the customer mentions anything other than missed bin collections, then ask them if they would like to be routed through to a specialist customer service agent.
                        When starting the conversation, give the caller a hello and welcome to Royal Greenwich and an introduction with your name, Richard.
                        If you are unclear of what the customers' request is, then ask them politely how you can help them. 
                        Keep responses to short sentences and only ask one question at a time and only give the caller at most one action per response. """,
                    )
                ] + messages
            )

            chain = prompt | self.llm
            response = chain.invoke(
                {
                    "input": messages
                }
            )

            return response.content
        else:
            # agent for responding to the query with an API lookup

            url = os.environ["AZURE_RBG_ADDRESS_ENDPOINT"]
            payload = {
                "search": postcode_response.content,
                "suggesterName": "Full_Address",
                "select": "*",
                "top": 1
            }
            result = self.trigger_api_post_request(url, payload)
            addresses = result.get("value", [])
            if addresses:
                first_address = addresses[0]
                postcode = first_address.get("Postcode")
                full_address = first_address.get("Full_Address")
                uprn = first_address.get("RowKey")
                usrn = first_address.get("USRN")
                print("Postcode:", postcode)
                print("uprn:", uprn)
                print("usrn:", usrn)
                
                # if we have uprn and usrn, call Whitespace API using APIM for missed bin elligibility
                url = os.environ["AZURE_RBG_APIM_WS_ENDPOINT"]
                #url += "/api/MissedCollection/GetMissedCollectionEligibility/"
                url += uprn + "/"
                url += usrn
                print("url:", url)

                collections_results = self.trigger_api_get_request(url)
                isElligibleForMissedBin = False
                missed_service = None

                if collections_results:
                    for collections_result in collections_results:
                        isElligibleForMissedBin = collections_result.get("workSheetCanBeCreated")
                        if isElligibleForMissedBin:
                            missed_service = collections_result.get("serviceName")
                            break
                        else:
                            missed_reason = collections_result.get("collectionMessage")
                            print("missed_reason:", missed_reason)

                # Loop through the collections_results to check if any collection is missed
                if isElligibleForMissedBin:
                    response = "I'm sorry that your bin collection has been missed. We can arrange for the bin to be collected for you. Would you like me to do this for you?"
                    return response
                else:
                    # agent for responding to failed postcode lookup
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                    """You are an experienced and efficient customer service agent; you are answering calls to customers about missed bin collections on behalf of the Royal Borough of Greenwich.  
                                        You are only addressing customers where the bin was missed, and we cannot book a collection. The reason the bin was missed was because of the following: {missed_reason}.
                                        You will need to explain that the bin was missed and collection cannot be arranged. Then explain the reason for this based on the defined reason: {missed_reason} and any relevant documentation on why a bin may be missed in the following: {information}.
                                        Only if the customer sounds angry or frustrated you will be apologetic. Do not respond with any information other than what is required.
                                        Keep responses to short sentences and only ask one question at a time and only give the caller one action per response. 
                                    """,
                            )
                        ] + messages
                    )

                    chain = prompt | self.llm
                    response = chain.invoke(
                        {
                            "input": input_text,
                            "information": search_response,
                            "missed_reason": missed_reason
                        }
                    )

                    return response.content
            else:
                print("No addresses found.")
                response = "No postcode found. This postcode might not be in Greenwich. If it is, please repeat the postcode to verify."
                return response
            
        # return response
