import os
import requests

def download_sample_pdf():
    # Apple Q3 2024 10-Q PDF URL from Investor Relations
    pdf_url = "https://s2.q4cdn.com/470004007/files/doc_financials/2024/q3/aapl-q324-10q.pdf"
    target_dir = "data/pdf/Apple/Q3-2024"
    os.makedirs(target_dir, exist_ok=True)
    dest_path = os.path.join(target_dir, "aapl-q324-10q.pdf")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Downloading real Apple 10-Q filing PDF from: {pdf_url}...")
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✓ Saved PDF to: {dest_path}")
            return True
        else:
            print(f"× Failed to download PDF. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"× Error downloading PDF: {e}")
        return False

def create_sample_audio_and_transcript():
    audio_dir = "data/audio/Apple/Q3-2024"
    transcript_dir = "data/transcripts/Apple/Q3-2024"
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(transcript_dir, exist_ok=True)
    
    # 1. Create a mock audio file (since we don't download 60MB raw audio here)
    # This is an empty placeholder wav file so the code registers that an audio file exists
    audio_path = os.path.join(audio_dir, "apple_q3_2024_earnings_call.wav")
    if not os.path.exists(audio_path):
        with open(audio_path, "wb") as f:
            f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x22\x56\x00\x00\x22\x56\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00")
        print(f"✓ Created sample audio file placeholder: {audio_path}")
        
    # 2. Create the corresponding transcript JSON file
    # This is what Whisper would output. It has timestamps and speaker diarization.
    transcript_path = os.path.join(transcript_dir, "apple_q3_2024_transcript.json")
    transcript_data = [
        {
            "text": "Good afternoon, this is Tim Cook. We are pleased to announce Apple's financial results for Q3 2024. Revenue reached 85.8 billion dollars, up 5% year-over-year. Our growth was driven by strong demand for Services and iPad.",
            "start": 0.0,
            "end": 18.0,
            "speaker": "Tim Cook"
        },
        {
            "text": "Gross margin was exceptional, coming in at 46.3% which reflects favorable mix shift and operational efficiency. We are very comfortable with our expense structure and see strong margins continuing.",
            "start": 18.0,
            "end": 35.0,
            "speaker": "Tim Cook"
        },
        {
            "text": "Now, turning to our balance sheet. We have outstanding liquidity. Regarding our short-term obligations and general debt capacity: our net cash position is extremely robust. We see absolutely zero risk of default or refinancing pressure. In fact, our operations generate cash flows that easily exceed all our obligations.",
            "start": 35.0,
            "end": 60.0,
            "speaker": "Tim Cook"
        }
    ]
    
    with open(transcript_path, "w") as f:
        import json
        json.dump(transcript_data, f, indent=2)
    print(f"✓ Created Whisper transcript output file: {transcript_path}")

if __name__ == "__main__":
    download_sample_pdf()
    create_sample_audio_and_transcript()
