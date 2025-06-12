import os
import dotenv

from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_community.document_loaders import Docx2txtLoader


dotenv.load_dotenv()

class SearchHandler:
    def __init__(self) -> None:

        self.embeddings = AzureOpenAIEmbeddings(
                azure_deployment=os.environ["AZURE_EMBEDDINGS_DEPLOYMENT_NAME"],
                openai_api_version=os.environ["EMBEDDINGS_OPENAI_API_VERSION"],
                azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )

        self.vector_store = AzureSearch(
                azure_search_endpoint=os.environ["AZURE_AI_SEARCH_SERVICE_NAME"],
                azure_search_key=os.environ["AZURE_AI_SEARCH_API_KEY"],
                index_name=os.environ["AZURE_AI_SEARCH_INDEX_NAME"],
                embedding_function=self.embeddings.embed_query,
        )

        self.llm = AzureChatOpenAI(
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
        )
    
    def create_vector_index(self):

        folder_path = "./docs/"
        for doc in os.listdir(folder_path):

            doc_path = os.path.join(folder_path, doc)
            if doc_path.endswith('.docx'):
                document = Docx2txtLoader(doc_path).load()
            elif doc_path.endswith('.pdf'):
                document = PyPDFLoader(doc_path).load()
            else:
                # Assuming other documents are plain text for simplicity
                loader = TextLoader(doc_path, encoding="utf-8")
                document = loader.load()

            text_splitter = CharacterTextSplitter(chunk_size=900, chunk_overlap=300)
            docs = text_splitter.split_documents(document)

            self.vector_store.add_documents(documents=docs)

    def get_query_response(self, input_text):

        docs = self.vector_store.similarity_search(query=input_text, k=3)

        if not docs:
            return (
                "I'm sorry, I couldn't find any relevant information. "
                "You can contact the council at 020 8921 4661 or email contact.centre@royalgreenwich.gov.uk for help."
            )

        # Combine top 3 results
        context = "\n\n".join([doc.page_content for doc in docs])
        return context

# Uncomment this to create or add to the vector index in AI search
# SearchHandler().create_vector_index()