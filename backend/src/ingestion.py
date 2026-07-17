import os
import json
import pdfplumber
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class Ingestor:
    def __init__(self, chroma_db_path=None):
        if chroma_db_path is None:
            # Resolve relative to the backend folder
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            chroma_db_path = os.path.join(base_dir, "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        # Initialize Gemini Client if key is available
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.genai_client = genai.Client(api_key=self.api_key)
        else:
            self.genai_client = None
            print("WARNING: GEMINI_API_KEY not found in environment. Ingestor will use local embeddings.")

        # Create or get collections
        self.pdf_collection = self.chroma_client.get_or_create_collection(
            name="pdf_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        self.audio_collection = self.chroma_client.get_or_create_collection(
            name="audio_chunks",
            metadata={"hnsw:space": "cosine"}
        )

    def get_embedding(self, text: str):
        """Generates embedding for a given text using Gemini or falls back to Chroma's default."""
        if self.genai_client:
            try:
                response = self.genai_client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                return response.embeddings[0].values  # type: ignore
            except Exception as e:
                print(f"Error calling Gemini embeddings API: {e}. Falling back to default.")
                return None
        return None

    def chunk_text(self, text: str, chunk_size=800, overlap=150):
        """Splits text into chunks with overlap."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    def process_pdf(self, pdf_path: str, company: str, quarter: str):
        """Parses PDF, chunks text, generates embeddings and loads into ChromaDB."""
        print(f"Parsing PDF: {pdf_path}")
        pages_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                tables = page.extract_tables()
                table_text = ""
                if tables:
                    for table in tables:
                        for row in table:
                            row_str = " | ".join([str(cell) if cell is not None else "" for cell in row])
                            table_text += row_str + "\n"
                pages_content.append({
                    "page_num": idx + 1,
                    "content": text + "\n" + table_text
                })
        
        # Ingest pages into ChromaDB
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        chunk_idx = 0
        for page in pages_content:
            page_chunks = self.chunk_text(page["content"])
            for sub_chunk in page_chunks:
                chunk_id = f"{company}_{quarter}_pdf_p{page['page_num']}_c{chunk_idx}"
                documents.append(sub_chunk)
                metadatas.append({
                    "company": company,
                    "quarter": quarter,
                    "source": "pdf",
                    "page_number": page["page_num"]
                })
                ids.append(chunk_id)
                
                # Check for Gemini Embeddings
                emb = self.get_embedding(sub_chunk)
                if emb:
                    embeddings.append(emb)
                chunk_idx += 1
                
        # Insert to Chroma
        if embeddings:
            self.pdf_collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        else:
            # Let Chroma compute default embeddings
            self.pdf_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        print(f"Ingested {len(ids)} PDF chunks into ChromaDB.")
        return len(ids)

    def process_audio_transcript(self, transcript_path_or_data, company: str, quarter: str):
        """Loads a timestamped audio transcript JSON/text into ChromaDB.
        The input can be a path to a transcript file or a direct JSON string/dict.
        """
        data = None
        if isinstance(transcript_path_or_data, str):
            if os.path.exists(transcript_path_or_data):
                with open(transcript_path_or_data, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        # Fallback if transcript is just text
                        f.seek(0)
                        raw_text = f.read()
                        data = [{"text": raw_text, "start": 0.0, "end": 0.0, "speaker": "CEO"}]
            else:
                try:
                    data = json.loads(transcript_path_or_data)
                except json.JSONDecodeError:
                    data = [{"text": transcript_path_or_data, "start": 0.0, "end": 0.0, "speaker": "CEO"}]
        elif isinstance(transcript_path_or_data, list):
            data = transcript_path_or_data
        elif isinstance(transcript_path_or_data, dict):
            data = transcript_path_or_data.get("segments", [transcript_path_or_data])
            
        if not data:
            print("No valid audio transcript data found.")
            return 0
            
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        
        for idx, segment in enumerate(data):
            text = segment.get("text", "")
            start = segment.get("start", 0.0)
            end = segment.get("end", 0.0)
            speaker = segment.get("speaker", "CEO")
            
            chunk_id = f"{company}_{quarter}_audio_s{idx}"
            documents.append(text)
            metadatas.append({
                "company": company,
                "quarter": quarter,
                "source": "audio",
                "start_time_seconds": start,
                "end_time_seconds": end,
                "speaker": speaker
            })
            ids.append(chunk_id)
            
            emb = self.get_embedding(text)
            if emb:
                embeddings.append(emb)
                
        # Insert to Chroma
        if embeddings:
            self.audio_collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        else:
            self.audio_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
        print(f"Ingested {len(ids)} audio chunks into ChromaDB.")
        return len(ids)
