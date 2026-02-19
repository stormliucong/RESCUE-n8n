import requests
import hashlib

def download_pdf(url, save_path):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded PDF: {save_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download PDF from {url}: {e}")
        return False

def calculate_md5(file_path):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"❌ Failed to calculate MD5 for {file_path}: {e}")
        return None