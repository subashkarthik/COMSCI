import os
import subprocess
import sys
import platform
import urllib.request
import zipfile

def setup_cloudflare():
    """Downloads and runs cloudflared for a stable HTTPS tunnel."""
    cwd = os.getcwd()
    bin_dir = os.path.join(cwd, "bin")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
        
    system = platform.system().lower()
    if "windows" in system:
        exe_path = os.path.join(bin_dir, "cloudflared.exe")
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    else:
        print("This script is optimized for Windows.")
        return

    if not os.path.exists(exe_path):
        print(f"[*] Downloading Cloudflare Tunnel tool...")
        try:
            urllib.request.urlretrieve(url, exe_path)
            print("[+] Download complete.")
        except Exception as e:
            print(f"[-] Download failed: {e}")
            return

    print("\n" + "="*50)
    print("      CLOUDFLARE TUNNEL (Stable & Free)")
    print("="*50)
    print("[*] Starting tunnel on port 8000...")
    print("[!] Look for the URL: https://[random-name].trycloudflare.com")
    print("[!] COPY THAT URL AND ADD /webhook TO THE END")
    print("="*50 + "\n")

    try:
        subprocess.run([exe_path, "tunnel", "--url", "http://localhost:8000"], check=True)
    except KeyboardInterrupt:
        print("\n[!] Tunnel closed.")
    except Exception as e:
        print(f"\n[-] Error running tunnel: {e}")

if __name__ == "__main__":
    setup_cloudflare()
