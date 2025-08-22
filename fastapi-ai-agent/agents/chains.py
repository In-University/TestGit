import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from PIL import Image
import pytesseract
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.docstore.document import Document
from agents.llm import LLMConfig
from app.services.s3_service import S3Service
from app.db.database import get_file_metadata_by_ids, get_db
from app.models.file_metadata import FileMetadata

class RAGChain:
    def __init__(self):
        self.llm_config = LLMConfig()
        self.embeddings = self.llm_config.get_embeddings()
        self.llm = self.llm_config.get_llm()
        self.user_vector_stores = {} # Store FAISS vector stores per user_id

    def _get_vector_store_path(self, user_id: int) -> str:
        """Generates a user-specific path for the FAISS vector store."""
        return f"faiss_index_{user_id}"

    def load_vector_store(self, user_id: int):
        """Loads a user-specific FAISS vector store if it exists."""
        path = self._get_vector_store_path(user_id)
        print(f"DEBUG: Attempting to load vector store for user {user_id} from path: {path}")
        if os.path.exists(path):
            print(f"DEBUG: Directory {path} exists. Listing contents before loading:")
            try:
                for root, dirs, files in os.walk(path):
                    for name in files:
                        print(f"DEBUG:   - {os.path.join(root, name)}")
                    for name in dirs:
                        print(f"DEBUG:   - {os.path.join(root, name)}/")
            except Exception as e:
                print(f"ERROR: Could not list contents of {path}: {e}")

            self.user_vector_stores[user_id] = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)
            print(f"Loaded vector store for user {user_id} from {path}")
        else:
            print(f"No vector store found for user {user_id} at {path}")
            self.user_vector_stores[user_id] = None

    def save_vector_store(self, user_id: int):
        """Saves the current FAISS vector store for a specific user."""
        if user_id in self.user_vector_stores and self.user_vector_stores[user_id] is not None:
            path = self._get_vector_store_path(user_id)
            self.user_vector_stores[user_id].save_local(path)
            print(f"Saved vector store for user {user_id} to {path}")
            if os.path.exists(path):
                print(f"DEBUG: Vector store directory confirmed to exist after save: {path}. Listing contents:")
                try:
                    for root, dirs, files in os.walk(path):
                        for name in files:
                            print(f"DEBUG:   - {os.path.join(root, name)}")
                        for name in dirs:
                            print(f"DEBUG:   - {os.path.join(root, name)}/")
                except Exception as e:
                    print(f"ERROR: Could not list contents of {path}: {e}")
            else:
                print(f"ERROR: Vector store directory NOT found after save: {path}")
        else:
            print(f"No vector store to save for user {user_id}")

    def process_document(self, file_path: str, file_type: str, user_id: int, file_id: int):
        """Loads a document, splits it into chunks, and creates/updates a RAG chain for a specific user."""
        documents = []
        try:
            # Always try to load the existing vector store first
            self.load_vector_store(user_id)
            if self.user_vector_stores[user_id] is None:
                print(f"DEBUG: No existing vector store found for user {user_id} on disk. A new one will be created.")

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

            # Add file_id to document metadata
            for doc in docs:
                doc.metadata["file_id"] = file_id
            print(f"DEBUG: Documents prepared for processing. First doc metadata: {docs[0].metadata if docs else 'N/A'}")

            # Now, self.user_vector_stores[user_id] will either contain the loaded store or be None.
            # Proceed to add documents or create a new store.
            if self.user_vector_stores[user_id] is not None:
                self.user_vector_stores[user_id].add_documents(docs)
                print(f"DEBUG: Merged {len(docs)} new documents with file_id {file_id} for user {user_id}.")
            else:
                self.user_vector_stores[user_id] = FAISS.from_documents(docs, self.embeddings)
                print(f"DEBUG: Created new vector store for user {user_id} with {len(docs)} documents from file_id {file_id}.")
            
            self.save_vector_store(user_id) # Save the updated/new vector store

            return True
        except Exception as e:
            print(f"ERROR: Error processing document for user {user_id}, file_id {file_id}: {e}")
            return False

    def get_qa_chain(self, user_id: int, file_ids: list[int] = None):
        """
        Returns the initialized QA chain for a specific user, optionally filtered by file_ids.
        If file_ids are provided, a temporary retriever is created.
        """
        print(f"DEBUG: get_qa_chain called for user_id: {user_id}, with file_ids: {file_ids}")

        if user_id not in self.user_vector_stores or self.user_vector_stores[user_id] is None:
            self.load_vector_store(user_id)
            if self.user_vector_stores[user_id] is None:
                print(f"DEBUG: No vector store available for user {user_id}.")
                return None

        base_retriever = self.user_vector_stores[user_id].as_retriever()

        if file_ids:
            print(f"DEBUG: Filtering vector store for user {user_id} by file_ids: {file_ids}")
            filtered_docs = []
            all_docs_in_store_ids = []
            for doc_id in self.user_vector_stores[user_id].index_to_docstore_id.values():
                doc = self.user_vector_stores[user_id].docstore.search(doc_id)
                if doc:
                    all_docs_in_store_ids.append(doc.metadata.get("file_id", "N/A"))
                    if doc.metadata.get("file_id") in file_ids:
                        filtered_docs.append(doc)
            
            print(f"DEBUG: All document IDs found in user's vector store: {all_docs_in_store_ids}")
            print(f"DEBUG: Number of documents after filtering by file_ids: {len(filtered_docs)}")

            if not filtered_docs:
                print(f"DEBUG: No documents found in vector store matching the provided file_ids: {file_ids}")
                return None # No documents found for the given file_ids

            # Create a temporary FAISS index from filtered documents
            temp_vector_store = FAISS.from_documents(filtered_docs, self.embeddings)
            retriever = temp_vector_store.as_retriever()
            print(f"DEBUG: Created temporary vector store with {len(filtered_docs)} documents.")
        else:
            print(f"DEBUG: No file_ids provided. Using base retriever for user {user_id}.")
            retriever = base_retriever

        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever
        )

class GeneratorChain:
    def __init__(self, qa_chain: RetrievalQA):
        if not qa_chain:
            raise ValueError("QA Chain must be initialized before GeneratorChain.")
        self.qa_chain = qa_chain

    def generate_flashcards(self, topic: str):
        """
        Generates professional flashcards based on the document and a given topic.
        Each flashcard includes a clear question on the front and a concise answer on the back.
        """
        prompt = f"""
        Based on the provided document, generate 5 professional flashcards about the topic: '{topic}'.
        Each flashcard should have a 'Front' (question) and a 'Back' (answer).
        Ensure the questions are clear and the answers are concise and directly relevant to the document.
        Format the output as a JSON array of objects, like this:
        [
            {{
                "front": "Question 1",
                "back": "Answer 1"
            }},
            {{
                "front": "Question 2",
                "back": "Answer 2"
            }}
        ]
        """
        try:
            print(f"DEBUG: Generating flashcards for topic: '{topic}'. Querying retriever with prompt snippet: '{prompt[:100]}...'")
            
            retrieved_docs = self.qa_chain.retriever.get_relevant_documents(prompt)
            print(f"DEBUG: Retrieved {len(retrieved_docs)} documents for flashcard generation.")
            for i, doc in enumerate(retrieved_docs):
                print(f"DEBUG: Document {i+1} (ID: {doc.metadata.get('file_id', 'N/A')}):")
                print(f"DEBUG: Content (first 200 chars): {doc.page_content[:200]}...")
                print(f"DEBUG: Metadata: {doc.metadata}")
            
            result = self.qa_chain.run(prompt)
            return result
        except Exception as e:
            raise Exception(f"Failed to generate flashcards: {e}")

    def generate_quiz(self, part: int):
        """
        Generates a professional TOEIC-style quiz question for a specific part.
        The question should be relevant to the document, and include four options (A, B, C, D)
        with one correct answer.
        """
        if not (1 <= part <= 7):
            raise ValueError("TOEIC part must be between 1 and 7.")

        prompt = f"""
        Based on the provided document, create one professional TOEIC-style multiple-choice question for Part {part}.
        The question should be challenging but fair, and directly related to the content.
        Provide four distinct answer options (A, B, C, D), only one of which is correct.
        Clearly indicate the correct answer.

        Format the output as a JSON object
        """
        try:
            # Debugging: Log what the retriever is fetching
            print(f"DEBUG: Generating quiz for part {part}. Querying retriever with prompt snippet: '{prompt[:100]}...'")
            
            # The RetrievalQA chain internally calls the retriever.
            # To explicitly see what's being retrieved, we can simulate the retrieval step.
            # Note: This might duplicate work if the QA chain also calls it, but it's for debugging.
            retrieved_docs = self.qa_chain.retriever.get_relevant_documents(prompt)
            print(f"DEBUG: Retrieved {len(retrieved_docs)} documents for quiz generation.")
            for i, doc in enumerate(retrieved_docs):
                print(f"DEBUG: Document {i+1} (ID: {doc.metadata.get('file_id', 'N/A')}):")
                print(f"DEBUG: Content (first 200 chars): {doc.page_content[:200]}...")
                print(f"DEBUG: Metadata: {doc.metadata}")
            
            result = self.qa_chain.run(prompt)
            return result
        except Exception as e:
            raise Exception(f"Failed to generate quiz: {e}")
