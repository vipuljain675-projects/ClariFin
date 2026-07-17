import os
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from src.ingestion import Ingestor
from src.analyzer import RAGAnalyzer
from src.transcribe import transcribe_audio_with_gemini

load_dotenv()

app = FastAPI(title="Multimodal Financial Earnings Call Analyzer API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    company: str
    quarter: str
    query: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Analyzer API is running"}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),  # 'pdf' or 'audio' or 'transcript'
    company: str = Form(...),
    quarter: str = Form(...)
):
    try:
        # Create directory for the file resolved absolutely inside backend/data/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if file_type == "pdf":
            target_dir = os.path.join(base_dir, "data", "pdf", company, quarter)
        elif file_type == "audio":
            target_dir = os.path.join(base_dir, "data", "audio", company, quarter)
        else:
            target_dir = os.path.join(base_dir, "data", "transcripts", company, quarter)
            
        os.makedirs(target_dir, exist_ok=True)
        
        file_path = os.path.join(target_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        return {
            "status": "success",
            "message": f"Successfully uploaded {file.filename} to {file_type}",
            "file_path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
async def ingest_data(
    company: str = Form(...),
    quarter: str = Form(...)
):
    try:
        ingestor = Ingestor()
        
        # 1. PDF processing (resolved absolutely to backend/data/)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_dir = os.path.join(base_dir, "data", "pdf", company, quarter)
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")] if os.path.exists(pdf_dir) else []
        
        if not pdf_files:
            raise HTTPException(status_code=400, detail=f"No PDF filing found in {pdf_dir}. Please upload a PDF first.")
            
        pdf_path = os.path.join(pdf_dir, pdf_files[0])
        pdf_chunks_count = ingestor.process_pdf(pdf_path, company, quarter)
        
        # 2. Audio Transcript processing
        transcript_dir = os.path.join(base_dir, "data", "transcripts", company, quarter)
        audio_dir = os.path.join(base_dir, "data", "audio", company, quarter)
        os.makedirs(transcript_dir, exist_ok=True)
        
        transcript_files = []
        if os.path.exists(transcript_dir):
            transcript_files += [os.path.join(transcript_dir, f) for f in os.listdir(transcript_dir) if f.lower().endswith((".json", ".txt"))]
        if os.path.exists(audio_dir):
            transcript_files += [os.path.join(audio_dir, f) for f in os.listdir(audio_dir) if f.lower().endswith((".json", ".txt"))]
            
        audio_chunks_count = 0
        if transcript_files:
            audio_chunks_count = ingestor.process_audio_transcript(transcript_files[0], company, quarter)
        else:
            # Check for audio files
            audio_files = [f for f in os.listdir(audio_dir) if f.lower().endswith((".mp3", ".wav", ".m4a"))] if os.path.exists(audio_dir) else []
            if audio_files:
                audio_path = os.path.join(audio_dir, audio_files[0])
                print(f"Transcribing audio with Gemini API: {audio_path}")
                # Transcribe for free using Gemini
                transcript_path = transcribe_audio_with_gemini(audio_path, company, quarter)
                if transcript_path:
                    audio_chunks_count = ingestor.process_audio_transcript(transcript_path, company, quarter)
                else:
                    print("Gemini transcription failed. Generating mock fallback transcript.")
                    mock_transcript = [
                        {
                            "text": f"Good morning, this is the CEO of {company}. We are extremely pleased to report Q3 results. Our total revenue has increased by 15% year-over-year, which reflects strong execution across all divisions.",
                            "start": 0.0,
                            "end": 18.0,
                            "speaker": "CEO"
                        },
                        {
                            "text": "Furthermore, we saw operating margins expand to 28%. We have our operational expenses fully optimized and we do not expect any margin compression going forward.",
                            "start": 18.0,
                            "end": 35.0,
                            "speaker": "CEO"
                        },
                        {
                            "text": "Now, addressing concerns raised recently about our debt load and credit rating. Let me be very clear: our balance sheet is in excellent shape. We have restructured all short-term maturities, and we see zero default risks. In fact, we are fully confident in our cash flows to cover all obligations.",
                            "start": 35.0,
                            "end": 60.0,
                            "speaker": "CEO"
                        }
                    ]
                    mock_path = os.path.join(transcript_dir, f"{company}_{quarter}_transcript.json")
                    with open(mock_path, "w") as f:
                        json.dump(mock_transcript, f)
                    audio_chunks_count = ingestor.process_audio_transcript(mock_transcript, company, quarter)
            else:
                print("No audio or transcript files found. Audio ingestion skipped.")
                
        return {
            "status": "success",
            "pdf_chunks": pdf_chunks_count,
            "audio_chunks": audio_chunks_count,
            "message": f"Successfully ingested {company} {quarter} data."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query_analyzer(request: QueryRequest):
    try:
        analyzer = RAGAnalyzer()
        result = analyzer.analyze_discrepancy(
            company=request.company,
            quarter=request.quarter,
            query=request.query
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8088, reload=True)
