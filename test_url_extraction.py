#!/usr/bin/env python
"""
Test script to verify URL extraction and conversion.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

from scribdl.selenium_downloader import ScribdSeleniumDownloader

def test_url_extraction():
    """Test various URL formats."""
    
    test_urls = [
        "https://www.scribd.com/document/799698609/Price-Action",
        "https://www.scribd.com/doc/799698609/Some-Title",
        "https://www.scribd.com/embeds/799698609/content",
        "https://www.scribd.com/document/123456789/Test-Document-With-Special-Chars-%3E%20",
    ]
    
    print("=" * 70)
    print("Testing URL Extraction and Conversion")
    print("=" * 70)
    
    for url in test_urls:
        print(f"\n📄 Input URL: {url}")
        doc_id = ScribdSeleniumDownloader._extract_doc_id(url)
        
        if doc_id:
            embed_url = f"https://www.scribd.com/embeds/{doc_id}/content"
            print(f"✅ Extracted ID: {doc_id}")
            print(f"🔗 Embed URL: {embed_url}")
        else:
            print("❌ Failed to extract ID")
        print("-" * 70)

if __name__ == "__main__":
    test_url_extraction()
