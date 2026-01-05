"""
Test script để kiểm tra phong cách phản hồi mới
"""

import colorama
from dotenv import load_dotenv
import time

load_dotenv()
colorama.init()

print("=" * 80)
print("PERSONALITY TEST - Bridge AI (Playful Mode)")
print("=" * 80)

try:
    from modules.llm_cloudflare import LLMCloudflareHandler
    
    llm = LLMCloudflareHandler()
    
    # Test cases với các tình huống khác nhau
    test_cases = [
        {
            "query": "Hey, how are you?",
            "emotion": None,
            "name": None,
            "description": "Casual greeting"
        },
        {
            "query": "I'm feeling tired today",
            "emotion": "sad",
            "name": "John",
            "description": "User is tired and sad"
        },
        {
            "query": "What's the weather like?",
            "emotion": "neutral",
            "name": "Sarah",
            "description": "Normal question"
        },
        {
            "query": "I'm so stressed about work!",
            "emotion": "stressed",
            "name": "Mike",
            "description": "Work stress"
        },
        {
            "query": "Tell me a joke",
            "emotion": "happy",
            "name": "Emma",
            "description": "Happy mood, wants fun"
        },
        {
            "query": "I'm worried about my exam tomorrow",
            "emotion": "fear",
            "name": "Alex",
            "description": "Anxious about exam"
        },
        {
            "query": "Guess what just happened!",
            "emotion": "surprise",
            "name": "Lisa",
            "description": "Excited/surprised"
        }
    ]
    
    print("\n" + colorama.Fore.CYAN + "Testing different scenarios..." + colorama.Style.RESET_ALL)
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_cases)}: {test['description']}")
        print(f"{'='*80}")
        
        # Context info
        context_parts = []
        if test['name']:
            context_parts.append(f"User: {test['name']}")
        if test['emotion']:
            context_parts.append(f"Emotion: {test['emotion']}")
        
        if context_parts:
            print(colorama.Fore.YELLOW + f"Context: {' | '.join(context_parts)}" + colorama.Style.RESET_ALL)
        
        print(colorama.Fore.BLUE + f"👤 User: {test['query']}" + colorama.Style.RESET_ALL)
        
        # Get response
        start = time.time()
        response = llm.chat(
            test['query'],
            user_emotion=test['emotion'],
            user_name=test['name']
        )
        duration = time.time() - start
        
        print(colorama.Fore.MAGENTA + f"🤖 Bridge: {response}" + colorama.Style.RESET_ALL)
        print(colorama.Fore.GREEN + f"⏱️  Response time: {duration:.2f}s" + colorama.Style.RESET_ALL)
        
        # Wait a bit between tests
        time.sleep(1)
    
    print("\n" + "="*80)
    print(colorama.Fore.GREEN + "✅ PERSONALITY TEST COMPLETE!" + colorama.Style.RESET_ALL)
    print("="*80)
    print()
    print("Đánh giá:")
    print("- Phong cách có vui vẻ, cợt nhã không?")
    print("- Có giữ được tính hữu ích không?")
    print("- Có phù hợp với emotion của user không?")
    print("- Độ dài câu trả lời có ngắn gọn không? (1-2 câu)")
    print()
    
except Exception as e:
    print(colorama.Fore.RED + f"❌ Test Failed: {e}" + colorama.Style.RESET_ALL)
    import traceback
    traceback.print_exc()
