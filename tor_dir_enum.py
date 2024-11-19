#!/usr/bin/env python3

import os
import sys
import threading
import queue
import requests
from requests.exceptions import RequestException

# Global Variables
TOR_PROXY = "socks5h://127.0.0.1:9050"  # Tor proxy address
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
TIMEOUT = 10  # Timeout for requests in seconds
THREAD_COUNT = 10  # Number of threads for enumeration
wordlist_path = "common.txt"  # Default wordlist path

# Banner
def banner():
    print("""
==================================================
    .onion Directory Enumerator
    Author: Jivitesh Khatri
    Advanced Features: Multi-threading, Logging
==================================================
""")

# Check Tor Connection
def check_tor_connection():
    try:
        print("[*] Checking Tor connection...")
        response = requests.get("http://check.torproject.org", proxies={"http": TOR_PROXY, "https": TOR_PROXY}, timeout=TIMEOUT)
        if "Congratulations. This browser is configured to use Tor." in response.text:
            print("[+] Tor is working correctly!")
        else:
            print("[-] Tor is not configured properly. Please ensure Tor is running.")
            sys.exit(1)
    except RequestException as e:
        print(f"[-] Error connecting to Tor: {e}")
        sys.exit(1)


def dir_enum_worker(target_url, word_queue, results, lock):
    while not word_queue.empty():
        word = word_queue.get()
        url = f"{target_url}/{word}"
        try:
            response = requests.get(url, proxies={"http": TOR_PROXY, "https": TOR_PROXY}, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            with lock:
                if response.status_code == 200:
                    results.append((url, response.status_code, len(response.content)))
                    print(f"[+] Found: {url} [Status: {response.status_code}, Size: {len(response.content)}]")
        except RequestException as e:
            with lock:
                print(f"[-] Error accessing {url}: {e}")
        word_queue.task_done()


def load_wordlist(wordlist_path):
    if not os.path.exists(wordlist_path):
        print(f"[-] Wordlist not found: {wordlist_path}")
        sys.exit(1)
    with open(wordlist_path, "r") as file:
        words = [line.strip() for line in file if line.strip()]
    print(f"[+] Loaded {len(words)} words from wordlist.")
    return words


def main():
    banner()

    
    check_tor_connection()

    
    target_url = input("[*] Enter .onion URL (e.g., http://exampleonion.onion): ").strip()
    if not target_url.endswith(".onion"):
        print("[-] Invalid .onion URL. Make sure it ends with .onion.")
        sys.exit(1)

    
    global wordlist_path
    wordlist_path = input("[*] Enter path to wordlist (default: common.txt): ").strip() or wordlist_path
    words = load_wordlist(wordlist_path)

    
    word_queue = queue.Queue()
    for word in words:
        word_queue.put(word)

    
    print("[*] Starting directory enumeration...")
    results = []
    lock = threading.Lock()
    threads = []

    for _ in range(THREAD_COUNT):
        thread = threading.Thread(target=dir_enum_worker, args=(target_url, word_queue, results, lock))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    
    output_file = "enumeration_results.txt"
    with open(output_file, "w") as file:
        for url, status, size in results:
            file.write(f"{url} [Status: {status}, Size: {size}]\n")

    print(f"[+] Enumeration complete. Results saved to {output_file}.")

if __name__ == "__main__":
    main()
