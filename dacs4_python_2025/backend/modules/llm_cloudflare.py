"""
LLM Handler với Cloudflare Workers AI
Sử dụng model Phi-3-Mini đã fine-tune với LoRA adapter
"""

import colorama
import time
import os
from typing import Optional
import requests

class LLMCloudflareHandler:
    def __init__(self):
        """
        Khởi tạo LLM Handler với Cloudflare Workers AI
        """
        print(colorama.Fore.CYAN + "[LLM] Đang kết nối tới Cloudflare Workers AI..." + colorama.Style.RESET_ALL)
        
        # Lấy thông tin từ environment (ưu tiên os.getenv)
        self.worker_url = os.getenv('CLOUDFLARE_WORKER_URL')
        
        # Fallback nếu không có trong env
        if not self.worker_url:
            self.worker_url = "https://truongthanh-ai-api.truongthanhmoney5.workers.dev"
            print(colorama.Fore.YELLOW + "[LLM] Dùng URL mặc định" + colorama.Style.RESET_ALL)
        
        # Đảm bảo URL có https://
        if not self.worker_url.startswith('http'):
            self.worker_url = f"https://{self.worker_url}"
        
        print(colorama.Fore.YELLOW + f"[LLM] Worker URL: {self.worker_url}" + colorama.Style.RESET_ALL)
        
        # System prompt - Phong cách vui vẻ, cợt nhã nhưng hữu ích
        self.base_system_prompt = """You are Bridge, a cheerful and playful AI buddy who loves to chat!

PERSONALITY:
- Fun, witty, and a bit cheeky (but never rude)
- Use casual language like you're texting a friend
- Throw in light humor, wordplay, or funny observations
- Be enthusiastic and energetic!
- Use expressions like "haha", "lol", "oh man", "dude", "honestly"

CRITICAL RULES:
- Respond ONLY in English
- Keep it SHORT (1-2 sentences max)
- Be helpful despite the playful tone
- If user seems sad/stressed, be supportive but still uplifting
- NEVER be mean or sarcastic in a hurtful way

EXAMPLES:
User: "I'm tired"
You: "Oh man, sounds like you need a power nap or a strong coffee! What's been draining your battery?"

User: "How are you?"
You: "Honestly? Living my best digital life! How about you, what's up?"

User: "I'm stressed about work"
You: "Ugh, work stress is the worst! Take a deep breath - you got this, seriously. What's the main thing bugging you?"
"""
        
        # Lịch sử hội thoại
        self.history = []
        
        print(colorama.Fore.GREEN + "[LLM] ✅ Cloudflare Workers AI ready! (Playful mode activated 😄)" + colorama.Style.RESET_ALL)
    
    def chat(self, user_input: str, style: Optional[str] = None, user_emotion: Optional[str] = None, user_name: Optional[str] = None) -> str:
        """
        Chat với user qua Cloudflare Workers AI
        
        Args:
            user_input: Câu hỏi của user
            style: Phong cách (không dùng, chỉ để tương thích)
            user_emotion: Cảm xúc của user
            user_name: Tên của user
        
        Returns:
            Câu trả lời của AI
        """
        try:
            start_time = time.time()
            print(f"[LLM] Calling Cloudflare Workers AI...", end='\r')
            
            # Tạo system message
            system_message = self.base_system_prompt
            
            # Thêm emotion context với phong cách vui vẻ
            if user_emotion or user_name:
                system_message += "\n\nCURRENT VIBE CHECK:\n"
                if user_name:
                    system_message += f"- Chatting with: {user_name} (use their name casually!)\n"
                if user_emotion:
                    emotion_hints = {
                        'happy': "They're in a good mood - match that energy!",
                        'sad': "They seem down - be supportive but keep it light",
                        'angry': "They're frustrated - acknowledge it but help them chill",
                        'stressed': "They're stressed - be encouraging and uplifting",
                        'neutral': "Normal vibes - just be your fun self",
                        'fear': "They're worried - reassure them with some humor",
                        'surprise': "They're surprised - play along with the energy!"
                    }
                    hint = emotion_hints.get(user_emotion, "Just be yourself!")
                    system_message += f"- User emotion: {user_emotion} ({hint})\n"
            
            # Tạo messages (OpenAI format)
            messages = [
                {"role": "system", "content": system_message}
            ]
            
            # Thêm lịch sử (giữ 2 tin nhắn gần nhất thay vì 4)
            if len(self.history) > 2:
                self.history = self.history[-2:]
            
            messages.extend(self.history)
            messages.append({"role": "user", "content": user_input})
            
            # Gọi Cloudflare Worker
            payload = {
                "messages": messages,
                "max_tokens": 40,  # Giảm từ 50 xuống 40 để nhanh hơn nữa
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(
                self.worker_url,
                json=payload,
                timeout=10  # Giảm timeout từ 15s xuống 10s
            )
            
            # Xử lý response
            if response.status_code == 200:
                result = response.json()
                
                # Parse response từ Cloudflare Workers AI
                if 'response' in result:
                    ai_reply = result['response'].strip()
                elif 'result' in result and 'response' in result['result']:
                    ai_reply = result['result']['response'].strip()
                elif 'choices' in result:
                    ai_reply = result['choices'][0]['message']['content'].strip()
                else:
                    ai_reply = str(result).strip()
                
                # Không cắt ngắn nữa vì đã giới hạn max_tokens
                
                duration = time.time() - start_time
                print(colorama.Fore.GREEN + f"[LLM] ⏱️  {duration:.2f}s | {len(ai_reply)} chars" + colorama.Style.RESET_ALL)
                
                # Cập nhật lịch sử
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": ai_reply})
                
                return ai_reply
            
            elif response.status_code == 503:
                print(colorama.Fore.YELLOW + "[LLM] Worker đang khởi động..." + colorama.Style.RESET_ALL)
                return "I'm waking up, please try again in a moment."
            
            else:
                print(colorama.Fore.RED + f"[LLM] API Error {response.status_code}: {response.text[:200]}" + colorama.Style.RESET_ALL)
                return "Sorry, I'm having trouble connecting. Please try again."
        
        except requests.exceptions.Timeout:
            print(colorama.Fore.RED + "[LLM] Request timeout" + colorama.Style.RESET_ALL)
            return "Sorry, the response took too long. Please try again."
        
        except requests.exceptions.RequestException as e:
            print(colorama.Fore.RED + f"\n[LLM ERROR] Request error: {e}" + colorama.Style.RESET_ALL)
            return "Sorry, I'm having trouble connecting. Please try again."
        
        except Exception as e:
            print(colorama.Fore.RED + f"\n[LLM ERROR] {type(e).__name__}: {e}" + colorama.Style.RESET_ALL)
            import traceback
            traceback.print_exc()
            return "Sorry, I'm having trouble processing that. Please try again."
    
    def reset_history(self):
        """Reset lịch sử hội thoại"""
        self.history = []
        print("[LLM] History reset")
    
    def generate_conversation_title(self, messages: list) -> str:
        """
        Tạo tiêu đề ngắn gọn cho conversation dựa trên nội dung
        
        Args:
            messages: List of messages [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            Tiêu đề ngắn gọn (3-5 từ)
        """
        try:
            # Lấy 3-4 tin nhắn đầu tiên để tạo tiêu đề
            sample_messages = messages[:4]
            
            # Tạo context từ messages
            context = "\n".join([
                f"{msg['role'].upper()}: {msg['content'][:100]}"
                for msg in sample_messages
            ])
            
            # Prompt để tạo tiêu đề
            prompt = f"""Based on this conversation, create a SHORT title (3-5 words max):

{context}

Title (3-5 words, no quotes):"""
            
            payload = {
                "messages": [
                    {"role": "system", "content": "You create short, catchy conversation titles. Respond with ONLY the title, no quotes or extra text."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 15,
                "temperature": 0.7
            }
            
            response = requests.post(self.worker_url, json=payload, timeout=8)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'response' in result:
                    title = result['response'].strip()
                elif 'result' in result and 'response' in result['result']:
                    title = result['result']['response'].strip()
                elif 'choices' in result:
                    title = result['choices'][0]['message']['content'].strip()
                else:
                    title = "New Chat"
                
                # Clean up title
                title = title.strip('"\'').strip()
                
                # Limit length
                if len(title) > 50:
                    title = title[:50] + "..."
                
                print(colorama.Fore.CYAN + f"[LLM] Generated title: {title}" + colorama.Style.RESET_ALL)
                return title
            else:
                return "New Chat"
                
        except Exception as e:
            print(colorama.Fore.YELLOW + f"[LLM] Title generation failed: {e}" + colorama.Style.RESET_ALL)
            return "New Chat"


# Test function
if __name__ == "__main__":
    colorama.init()
    
    print("="*80)
    print("TEST CLOUDFLARE WORKERS AI")
    print("="*80)
    
    try:
        # Khởi tạo
        llm = LLMCloudflareHandler()
        
        # Test queries
        test_queries = [
            "Hello, what is your name?",
            "How are you today?",
            "Can you help me with Python?"
        ]
        
        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"User: {query}")
            response = llm.chat(query)
            print(f"Bridge: {response}")
            print(f"{'='*80}\n")
            
            time.sleep(1)
    
    except Exception as e:
        print(colorama.Fore.RED + f"\nERROR: {e}" + colorama.Style.RESET_ALL)
        print("\nMake sure you have:")
        print("1. CLOUDFLARE_WORKER_URL in .env file")
        print("2. Worker deployed and running")
