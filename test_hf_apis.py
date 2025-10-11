#!/usr/bin/env python3

import requests
import json

HF_TOKEN = "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"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def test_hf_stt():
    print("🗣️ Testing HF STT API (Whisper)...")
    # For STT, we need audio data, but for test, we can check the model info
    url = "https://api-inference.huggingface.co/models/openai/whisper-tiny"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        print("✅ HF STT API accessible")
        return True
    else:
        print(f"❌ HF STT API failed: {response.status_code} - Model not available on free Inference API")
        return False

def test_hf_nlp():
    print("🧠 Testing HF NLP API (GPT-2)...")
    url = "https://api-inference.huggingface.co/models/gpt2"
    payload = {"inputs": "Hello, how are you?"}
    # Try without token first
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and result:
            print(f"✅ HF NLP API working: {result[0].get('generated_text', '')[:50]}...")
            return True
        else:
            print("❌ HF NLP API returned unexpected format")
            return False
    else:
        print(f"❌ HF NLP API failed: {response.status_code} - {response.text}")
        return False

def test_hf_tts():
    print("🔊 Testing HF TTS API...")
    # TTS might not be available on free Inference API
    url = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
    payload = {"inputs": "Hello world"}
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print("✅ HF TTS API working (returned audio data)")
        return True
    else:
        print(f"❌ HF TTS API failed: {response.status_code} - TTS may require paid Inference API")
        return False

def main():
    print("🧪 Testing HuggingFace APIs with provided token...\n")

    stt_ok = test_hf_stt()
    nlp_ok = test_hf_nlp()
    tts_ok = test_hf_tts()

    print("\n📊 Results:")
    print(f"STT API: {'✅' if stt_ok else '❌'}")
    print(f"NLP API: {'✅' if nlp_ok else '❌'}")
    print(f"TTS API: {'✅' if tts_ok else '❌'}")

    if all([stt_ok, nlp_ok, tts_ok]):
        print("\n🎉 All HF APIs are working! Ready for Auralis online mode.")
    else:
        print("\n⚠️ Some HF APIs failed. Check token or network.")

if __name__ == "__main__":
    main()