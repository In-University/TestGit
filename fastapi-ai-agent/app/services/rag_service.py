import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from PIL import Image
import pytesseract
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from app.core.config import GOOGLE_API_KEY
from langchain.docstore.document import Document

class RAGService:
    def __init__(self):
        self.vector_store = None
        self.qa_chain = None
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=GOOGLE_API_KEY)

    def process_document(self, file_path: str, file_type: str):
        """Loads a document, splits it into chunks, and creates a RAG chain."""
        documents = []
        try:
            if file_type == "application/pdf":
                loader = PyPDFLoader(file_path)
                documents = loader.load()
            elif file_type == "text/plain":
                loader = TextLoader(file_path)
                documents = loader.load()
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                loader = Docx2txtLoader(file_path)
                documents = loader.load()
            elif file_type.startswith("image/"):
                # For images, perform OCR
                text = pytesseract.image_to_string(Image.open(file_path))
                documents = [Document(page_content=text)]
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            docs = text_splitter.split_documents(documents)

            self.vector_store = FAISS.from_documents(docs, self.embeddings)
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever()
            )
            return True
        except Exception as e:
            print(f"Error processing document: {e}")
            return False

    def get_qa_chain(self):
        """Returns the initialized QA chain."""
        return self.qa_chain
