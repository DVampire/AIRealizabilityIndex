#!/usr/bin/env python3
"""
Debug script to compare local vs Hugging Face deployment
"""

import requests
import json
from datetime import date
import time

def test_local_api():
    """Test local API"""
    print("🔍 Testing LOCAL API...")
    try:
        
        # Test daily endpoint
        today = date.today().isoformat()
        daily_response = requests.get(f"http://localhost:7860/api/daily?date_str={today}", timeout=30)
        print(f"Local daily status: {daily_response.status_code}")
        
        if daily_response.ok:
            data = daily_response.json()
            cards = data.get('cards', [])
            cards_with_arxiv = [c for c in cards if c.get('arxiv_id')]
            print(f"Local: {len(cards_with_arxiv)}/{len(cards)} cards have arxiv_id")
            
            # Show first card details
            if cards:
                first_card = cards[0]
                print(f"Local first card arxiv_id: {first_card.get('arxiv_id', 'MISSING')}")
                print(f"Local first card URL: {first_card.get('huggingface_url', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Local API error: {e}")

def test_hf_api():
    """Test Hugging Face API"""
    print("\n🔍 Testing HUGGING FACE API...")
    try:
        base_url = "https://zwt963-paperindex.hf.space"
        
        
        # Test daily endpoint
        today = date.today().isoformat()
        print(f"HF daily endpoint: {base_url}/api/daily?date_str={today}")
        daily_response = requests.get(f"{base_url}/api/daily?date_str={today}", timeout=30)
        print(f"HF daily status: {daily_response.status_code}")
        
        if daily_response.ok:
            data = daily_response.json()
            cards = data.get('cards', [])
            cards_with_arxiv = [c for c in cards if c.get('arxiv_id')]
            print(f"HF: {len(cards_with_arxiv)}/{len(cards)} cards have arxiv_id")
            
            # Show first card details
            if cards:
                first_card = cards[0]
                print(f"HF first card arxiv_id: {first_card.get('arxiv_id', 'MISSING')}")
                print(f"HF first card URL: {first_card.get('huggingface_url', 'N/A')}")
        
    except Exception as e:
        print(f"❌ HF API error: {e}")

def test_direct_hf_access():
    """Test direct access to Hugging Face papers page"""
    print("\n🔍 Testing DIRECT Hugging Face access...")
    try:
        # Test accessing a specific paper page
        paper_url = "https://huggingface.co/papers/2508.07901"
        response = requests.get(paper_url, timeout=10)
        print(f"Direct HF paper access status: {response.status_code}")
        
        if response.ok:
            # Look for arXiv ID in the page
            content = response.text
            if "arxiv:2508.07901" in content:
                print("✅ Found arxiv:2508.07901 in page content")
            else:
                print("❌ arxiv:2508.07901 not found in page content")
                
            # Look for any arXiv references
            if "arxiv.org" in content:
                print("✅ Found arxiv.org references in page content")
            else:
                print("❌ No arxiv.org references found in page content")
        
    except Exception as e:
        print(f"❌ Direct HF access error: {e}")

if __name__ == "__main__":
    print("🚀 Starting comparison debug...")
    
    # Test local API (if running)
    test_local_api()
    
    # Test Hugging Face API
    test_hf_api()
    
    # Test direct Hugging Face access
    test_direct_hf_access()
    
    print("\n💡 Possible solutions:")
    print("1. Check if Hugging Face Space is using cached code")
    print("2. Verify network access from Hugging Face to external sites")
    print("3. Check if Hugging Face has different Python/package versions")
    print("4. Try redeploying the Space to clear any caches")