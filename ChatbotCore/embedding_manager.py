# embedding_manager.py
import os
import json
import hashlib
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from pypdf import PdfReader
from pathlib import Path

class EmbeddingManager:
    def __init__(self, storage_path="embeddings", collection_name="T3V-collection"):
        """Initialize the embedding manager with storage path and collection name."""
        self.storage_path = storage_path
        self.collection_name = collection_name
        self.metadata_path = os.path.join(storage_path, "metadata.json")
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize embedding function
        self.embedding_function = SentenceTransformerEmbeddingFunction()
        
        # Initialize chromadb client
        self.chroma_client = chromadb.PersistentClient(path=storage_path)
        
        # Initialize or load metadata
        self.metadata = self.load_metadata()
        
        # Initialize collection
        self.initialize_collection()
    
    def load_metadata(self):
        """Load metadata from file or create default metadata."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        else:
            default_metadata = {
                "files_processed": {},
                "last_updated": None,
                "document_count": 0
            }
            self.save_metadata(default_metadata)
            return default_metadata
    
    def save_metadata(self, metadata=None):
        """Save metadata to file."""
        if metadata is None:
            metadata = self.metadata
        
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def initialize_collection(self):
        """Initialize or load the ChromaDB collection."""
        try:
            self.collection = self.chroma_client.get_collection(
                self.collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Using existing collection with {self.collection.count()} documents")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                self.collection_name,
                embedding_function=self.embedding_function
            )
            print(f"Created new collection: {self.collection_name}")
    
    def process_pdf(self, pdf_path):
        """Process a PDF file and add to collection if needed."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"❌ File không tồn tại: {pdf_path}")
            return False
        
        # Calculate hash to check for changes
        file_hash = self.calculate_file_hash(pdf_path)
        file_key = str(pdf_path)
        
        # Check if file has been processed and hasn't changed
        if file_key in self.metadata["files_processed"] and self.metadata["files_processed"][file_key] == file_hash:
            print(f"File {pdf_path} already processed and unchanged, skipping.")
            return True
        
        try:
            # PDF loading
            reader = PdfReader(str(pdf_path))
            pdf_texts = [p.extract_text().strip() for p in reader.pages]
            pdf_texts = [text for text in pdf_texts if text]  # Filter empty strings
            
            # Text splitting - character based first
            character_splitter = RecursiveCharacterTextSplitter(
                separators=["\n\n", "\n", ". ", " ", ""],
                chunk_size=1000,
                chunk_overlap=0
            )
            character_split_text = character_splitter.split_text("\n\n".join(pdf_texts))
            
            # Then token-based splitting
            token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)
            token_split_texts = []
            for text in character_split_text:
                token_split_texts += token_splitter.split_text(text)
            
            # Remove existing documents from this file if any
            if file_key in self.metadata["files_processed"]:
                # In a real implementation, you would delete specific IDs related to this file
                # For simplicity, we'll recreate the collection if file changed
                print(f"File {pdf_path} has changed, updating embeddings.")
            
            # Add the new text chunks
            start_id = self.metadata["document_count"]
            ids = [str(i + start_id) for i in range(len(token_split_texts))]
            
            # Add metadata to track source
            metadatas = [{"source": file_key} for _ in token_split_texts]
            
            # Add to collection
            self.collection.add(
                ids=ids, 
                documents=token_split_texts,
                metadatas=metadatas
            )
            
            # Update metadata
            self.metadata["files_processed"][file_key] = file_hash
            self.metadata["document_count"] += len(token_split_texts)
            import datetime
            self.metadata["last_updated"] = datetime.datetime.now().isoformat()
            self.save_metadata()
            
            print(f"✅ Processed {pdf_path}: Added {len(token_split_texts)} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Error processing {pdf_path}: {e}")
            return False
    
    def get_collection(self):
        """Return the ChromaDB collection for use in applications."""
        return self.collection

# Usage example
if __name__ == "__main__":
    manager = EmbeddingManager()
    pdf_path = Path(__file__).parent / "data" / "T3V Chatbot Training Data.pdf"
    manager.process_pdf(pdf_path)