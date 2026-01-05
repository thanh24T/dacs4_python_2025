"""
Test script để đo tốc độ của từng component
"""

import time
import colorama
from dotenv import load_dotenv

load_dotenv()
colorama.init()

print("=" * 80)
print("SPEED TEST - AI VOICE CHAT COMPONENTS")
print("=" * 80)

# Test 1: LLM Speed
print("\n[1/2] Testing LLM (Cloudflare Workers AI)...")
try:
    from modules.llm_cloudflare import LLMCloudflareHandler
    
    llm = LLMCloudflareHandler()
    
    test_queries = [
        "Hello, how are you?",
        "What's the weather like?",
        "Tell me a joke"
    ]
    
    llm_times = []
    for query in test_queries:
        start = time.time()
        response = llm.chat(query)
        duration = time.time() - start
        llm_times.append(duration)
        print(f"  Query: '{query}'")
        print(f"  Response: '{response}'")
        print(f"  Time: {duration:.2f}s")
        print()
    
    avg_llm = sum(llm_times) / len(llm_times)
    print(colorama.Fore.GREEN + f"✅ LLM Average: {avg_llm:.2f}s" + colorama.Style.RESET_ALL)
    
except Exception as e:
    print(colorama.Fore.RED + f"❌ LLM Test Failed: {e}" + colorama.Style.RESET_ALL)

# Test 2: TTS Speed
print("\n[2/2] Testing TTS (ElevenLabs Turbo)...")
try:
    from modules.tts import TextToSpeech
    
    tts = TextToSpeech()
    
    test_texts = [
        "Hello, how are you today?",
        "The weather is nice.",
        "That's a great question!"
    ]
    
    tts_times = []
    for text in test_texts:
        start = time.time()
        audio = tts.generate_audio_bytes(text)
        duration = time.time() - start
        tts_times.append(duration)
        print(f"  Text: '{text}' ({len(text)} chars)")
        print(f"  Audio: {len(audio) if audio else 0} bytes")
        print(f"  Time: {duration:.2f}s")
        print(f"  Speed: {len(text)/duration:.1f} chars/sec")
        print()
    
    avg_tts = sum(tts_times) / len(tts_times)
    print(colorama.Fore.GREEN + f"✅ TTS Average: {avg_tts:.2f}s" + colorama.Style.RESET_ALL)
    
except Exception as e:
    print(colorama.Fore.RED + f"❌ TTS Test Failed: {e}" + colorama.Style.RESET_ALL)

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
try:
    total_avg = avg_llm + avg_tts
    print(f"Average LLM:   {avg_llm:.2f}s")
    print(f"Average TTS:   {avg_tts:.2f}s")
    print(f"Total Latency: {total_avg:.2f}s (excluding STT)")
    print()
    
    if total_avg < 2.0:
        print(colorama.Fore.GREEN + "🚀 EXCELLENT! Very fast response time." + colorama.Style.RESET_ALL)
    elif total_avg < 3.0:
        print(colorama.Fore.YELLOW + "✅ GOOD! Acceptable response time." + colorama.Style.RESET_ALL)
    else:
        print(colorama.Fore.RED + "⚠️  SLOW! Consider optimization." + colorama.Style.RESET_ALL)
except:
    pass

print("=" * 80)
