import os
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class RAGAnalyzer:
    def __init__(self, chroma_db_path=None):
        if chroma_db_path is None:
            # Resolve relative to the backend folder
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            chroma_db_path = os.path.join(base_dir, "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.genai_client = genai.Client(api_key=self.api_key)
        else:
            self.genai_client = None
            print("WARNING: GEMINI_API_KEY not found in RAGAnalyzer.")

        self.pdf_collection = self.chroma_client.get_collection("pdf_chunks")
        self.audio_collection = self.chroma_client.get_collection("audio_chunks")

    def get_embedding(self, text: str):
        if self.genai_client:
            try:
                response = self.genai_client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                return response.embeddings[0].values  # type: ignore
            except Exception as e:
                print(f"Error generating embedding: {e}")
                return None
        return None

    def query_context(self, company: str, quarter: str, query: str, n_results=5):
        """Retrieves relevant contexts from both PDF and Audio collections."""
        query_emb = self.get_embedding(query)
        
        # Build filters
        filter_dict = {
            "$and": [
                {"company": {"$eq": company}},
                {"quarter": {"$eq": quarter}}
            ]
        }
        
        # Query PDF chunks
        if query_emb:
            pdf_results = self.pdf_collection.query(
                query_embeddings=[query_emb],
                where=filter_dict,  # type: ignore
                n_results=n_results
            )
            audio_results = self.audio_collection.query(
                query_embeddings=[query_emb],
                where=filter_dict,  # type: ignore
                n_results=n_results
            )
        else:
            pdf_results = self.pdf_collection.query(
                query_texts=[query],
                where=filter_dict,  # type: ignore
                n_results=n_results
            )
            audio_results = self.audio_collection.query(
                query_texts=[query],
                where=filter_dict,  # type: ignore
                n_results=n_results
            )
            
        return pdf_results, audio_results

    def analyze_discrepancy(self, company: str, quarter: str, query: str):
        """Retrieves contexts, structures prompt, and calls Gemini to compare."""
        if not self.genai_client:
            return {"error": "Gemini API key is not configured."}
            
        pdf_res, audio_res = self.query_context(company, quarter, query)
        
        pdf_docs = pdf_res.get("documents", [[]])[0]  # type: ignore
        pdf_meta = pdf_res.get("metadatas", [[]])[0]  # type: ignore
        
        audio_docs = audio_res.get("documents", [[]])[0]  # type: ignore
        audio_meta = audio_res.get("metadatas", [[]])[0]  # type: ignore
        
        # Format the retrieved contexts
        pdf_context_str = ""
        for i, (doc, meta) in enumerate(zip(pdf_docs, pdf_meta)):
            page = meta.get("page_number", "Unknown")
            pdf_context_str += f"[Chunk {i+1} - PDF Page {page}]:\n{doc}\n\n"
            
        audio_context_str = ""
        for i, (doc, meta) in enumerate(zip(audio_docs, audio_meta)):
            start = meta.get("start_time_seconds", 0.0)
            end = meta.get("end_time_seconds", 0.0)
            speaker = meta.get("speaker", "CEO")
            audio_context_str += f"[Chunk {i+1} - Audio {start:.1f}s - {end:.1f}s | Speaker: {speaker}]:\n{doc}\n\n"
            
        if not pdf_context_str and not audio_context_str:
            return {
                "response": "No matching filing or audio context found in the database. Please verify if ingestion was completed successfully.",
                "pdf_context": [],
                "audio_context": []
            }
            
        # Construct Prompt
        prompt = f"""You are a professional financial forensic auditor and analyst. Your task is to cross-examine a company's written financial reports (10-Q/10-K filings) with their spoken earnings call transcript to find contradictions, omissions, or significant shifts in tone and sentiment.

Query to analyze: "{query}"

Here is the retrieved context:

=== WRITTEN FINANCIAL FILING (PDF) ===
{pdf_context_str}

=== SPOKEN EARNINGS CALL (AUDIO/TRANSCRIPT) ===
{audio_context_str}

Please generate an analysis structured with:
1. **Direct Contradictions & Discrepancies**: Compare facts and figures. Do they differ? Note any hard mismatches.
2. **Omissions & Additions**: Did the CEO mention positive achievements that aren't backed up in the text, or did they omit key risk factors in the audio that are prominently stated in the written filing?
3. **Sentiment & Tone Shifts**: Assess if the written reports are cautious/pessimistic while the CEO's spoken tone is overly confident/optimistic.
4. **Summary & Verification Status**: A final verdict on whether the spoken statements align with the filings for this query.

Provide exact citations (like "PDF Page X" or "Audio Y seconds") for all assertions.
"""

        try:
            # Using Gemini 2.5 Flash as the standard medium model (or 1.5 Pro if we want deep analysis)
            response = self.genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            return {
                "response": response.text,
                "pdf_context": [{"text": doc, "meta": meta} for doc, meta in zip(pdf_docs, pdf_meta)],
                "audio_context": [{"text": doc, "meta": meta} for doc, meta in zip(audio_docs, audio_meta)]
            }
        except Exception as e:
            return {"error": f"Failed to call Gemini API: {str(e)}"}
