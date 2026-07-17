import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

class TranscriptSegment(BaseModel):
    text: str = Field(description="The exact words spoken in this segment")
    start: float = Field(description="Start time in seconds from the beginning of the audio")
    end: float = Field(description="End time in seconds from the beginning of the audio")
    speaker: str = Field(description="The speaker identity if identifiable, e.g., 'CEO', 'CFO', or 'Speaker'")

class FullTranscript(BaseModel):
    segments: List[TranscriptSegment]

def transcribe_audio_with_gemini(audio_path: str, company: str, quarter: str):
    """Transcribes audio using Gemini's native audio capabilities for free."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        return None
        
    client = genai.Client(api_key=api_key)
    
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return None
        
    print(f"Uploading audio file '{audio_path}' to Google GenAI storage...")
    try:
        # Upload the audio file to Google Cloud using Gemini Files API
        audio_file = client.files.upload(file=audio_path)
        print(f"Uploaded successfully. File name on server: {audio_file.name}")
        
        # Wait until the file is fully processed on Google's end
        print("Waiting for file processing to complete...")
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = client.files.get(name=audio_file.name)
            
        if audio_file.state.name == "FAILED":
            raise Exception("File processing failed on Google servers.")
            
        print("File is ready. Generating timestamped transcript using Gemini...")
        
        prompt = "Generate a detailed timestamped transcript of this audio call. Break it down into segments of roughly 15-30 seconds or natural pauses. Identify who is speaking (e.g., CEO, Analyst, or Speaker)."
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[audio_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FullTranscript
            )
        )
        
        # Clean up the file from Google cloud storage once transcribed
        print("Cleaning up file from Google Cloud storage...")
        client.files.delete(name=audio_file.name)
        
        # Parse the structured JSON response
        result_json = json.loads(response.text)
        segments = result_json.get("segments", [])
        
        # Save transcript to data/transcripts/
        dest_dir = f"data/transcripts/{company}/{quarter}"
        os.makedirs(dest_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        dest_path = os.path.join(dest_dir, f"{base_name}_transcript.json")
        
        with open(dest_path, "w") as f:
            json.dump(segments, f, indent=2)
            
        print(f"✓ Successfully generated and saved transcript to: {dest_path}")
        return dest_path
        
    except Exception as e:
        print(f"× Error during Gemini transcription: {e}")
        return None

if __name__ == "__main__":
    # Test execution
    # transcribe_audio_with_gemini("data/audio/Apple/Q3-2024/apple_q3_2024_earnings_call.wav", "Apple", "Q3-2024")
    pass
