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
    
    def trigger_api_request(self,url, payload):
        headers = {
            "api-key": os.environ["AZURE_RBG_ADDRESS_KEY"],
            "Ocp-Apim-Subscription-Key": os.environ["AZURE_RBG_APIM_WS_KEY"],
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
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

        messages = self.parse_conversation(input_text)
        search_response = search_handler.get_query_response(input_text)
        
        # bot for extracting the postcode
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a bot for extracting the customer's postcode and house number (or name) from previous messages in a customer service conversation with a user.
                    The postcode format should be between 5 and 7 characters long and contain a space. e,.g. "AB12 3CD".
                    The house name/number should either be an integer, or at least 1 word.
                    Respond in JSON format (no newlines or whitespace) with an object containing "postcode", "name" and "number" properties.
                    If any property is not found, set the value for that property to 0.
                    """,
                )
            ] + messages
        )
        chain = prompt | self.llm
        postcode_response = chain.invoke(
            {"input": input_text}
        )

        # agent for pulling out the full postcode if not yet provided
        address_details = json.loads(postcode_response.content)
        if address_details['postcode'] == 0 or (address_details['name'] == 0 and address_details['number'] == 0):
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a sympathatic assistant that is responsible for deciding if its a missed bin query and if it is then ask for the full postcode and house number or name.                        """,
                    )
                ] + messages
            )

            chain = prompt | self.llm
            response = chain.invoke(
                {
                    "input": input_text,
                    "information": search_response
                }
            )

            return response.content
        else:
            # agent for responding to the query with an API lookup
            # - postcode and house number have been provided

            url = os.environ["AZURE_RBG_ADDRESS_ENDPOINT"]
            payload = {
                "search": address_details['postcode'],
                "suggesterName": "Full_Address",
                "select": "*",
                "top": 50
            }
            result = self.trigger_api_request(url, payload)
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
                # url = os.environ["AZURE_RBG_APIM_WS_ENDPOINT"]
                # url += "/api/MissedCollection/GetMissedCollectionEligibility/"
                # url += uprn + "/"
                # url += usrn
                # print("url:", url)
                # result = self.trigger_api_request(url, payload)
                # print("url:", url)
                # isElligible = result.get("value", [])

                # if isElligible:
                #     response = "You are eligible for a missed bin collection. Please contact the council to arrange this."
                #     return response
                # else:
                
                #     prompt = ChatPromptTemplate.from_messages(
                #         [
                #             (
                #                 "system",
                #                     """You are a sympathatic assistant that is responsible for addressing queries about bin collections but we could not verify from the given postcode.
                #                     This postcode might not be in Greenwich or you verify the postcode and try again
                #                     """,
                #             )
                #         ] + messages
                #     )

                #     chain = prompt | self.llm
                #     response = chain.invoke(
                #         {
                #             "input": input_text,
                #             "information": search_response
                #         }
                #     )

                response = "You are eligible for a missed bin collection. Please contact the council to arrange this."
                return response
            else:
                print("No addresses found.")
                response = "No postcode found. This postcode might not be in Greenwich or please verify the postcode again ."
                return response
