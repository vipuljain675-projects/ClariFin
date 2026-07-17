import os
import requests

def download_file(url: str, dest_path: str):
    """Downloads a file from a URL to a local destination path."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    print(f"Downloading from {url} to {dest_path}...")
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {dest_path}")
        return True
    else:
        print(f"Failed to download. Status code: {response.status_code}")
        return False
