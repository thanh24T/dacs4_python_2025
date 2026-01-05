"""
Face Recognition + Emotion Detection Module
- Nhận diện khuôn mặt (DeepFace)
- Phát hiện cảm xúc từ khuôn mặt (DeepFace)
- Lưu và load user profiles từ MySQL database
"""

import os
# Set environment variables before importing TensorFlow-dependent libraries
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import numpy as np
from deepface import DeepFace
import colorama
from typing import Optional, Dict, List
import cv2


class FaceEmotionDetector:
    def __init__(self, database=None):
        print(colorama.Fore.CYAN + "[FACE] Initializing Face Recognition + Emotion Detection..." + colorama.Style.RESET_ALL)
        
        self.database = database  # MySQL database instance
        self.recognition_threshold = 0.4  # ✅ Cosine similarity threshold (higher = stricter, typical: 0.4-0.6)
        
        print(colorama.Fore.YELLOW + "[FACE] Using ArcFace model (highest accuracy)" + colorama.Style.RESET_ALL)
        
        # Emotion mapping - Phong cách vui vẻ, cợt nhã
        self.emotion_responses = {
            'happy': "Yooo, someone's in a good mood! Love the energy!",
            'sad': "Aww, you look a bit down. Wanna talk about it? I'm all ears!",
            'angry': "Whoa, someone woke up on the wrong side of the bed! Deep breaths, buddy.",
            'fear': "Hey hey, you look worried! Everything cool? I got your back!",
            'surprise': "Haha, that face! What just happened? Spill the tea!",
            'neutral': "Chillin' vibes today, huh? What's on your mind?",
            'disgust': "Oof, that expression! Something bugging you or did you just smell something funky?"
        }
        
        print(colorama.Fore.GREEN + "[FACE] ✅ Ready!" + colorama.Style.RESET_ALL)
    
    def extract_face_embedding(self, image_bytes: bytes) -> Optional[List[float]]:
        """Extract face embedding from image"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Extract face embedding using ArcFace (most accurate model)
            embedding_objs = DeepFace.represent(
                img_path=img,
                model_name="ArcFace",  # ✅ Changed from Facenet to ArcFace for better accuracy
                enforce_detection=False
            )
            
            if not embedding_objs:
                return None
            
            return embedding_objs[0]["embedding"]
            
        except Exception as e:
            print(colorama.Fore.YELLOW + f"[FACE] Error extracting embedding: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def recognize_user(self, image_bytes: bytes) -> Optional[Dict]:
        """
        Nhận diện user từ database
        
        Returns:
            User dict nếu match, None nếu không match (user mới)
        """
        if not self.database:
            print(colorama.Fore.YELLOW + "[FACE] No database connected" + colorama.Style.RESET_ALL)
            return None
        
        try:
            # Extract embedding từ ảnh hiện tại
            current_embedding = self.extract_face_embedding(image_bytes)
            if current_embedding is None:
                return None
            
            current_embedding = np.array(current_embedding)
            
            # Normalize for cosine similarity
            current_embedding = current_embedding / np.linalg.norm(current_embedding)
            
            # Lấy tất cả users từ database
            users = self.database.get_all_users()
            if not users:
                print(colorama.Fore.YELLOW + "[FACE] No users in database" + colorama.Style.RESET_ALL)
                return None
            
            # So sánh với từng user
            best_match = None
            best_similarity = -1  # Cosine similarity: -1 to 1 (higher is better)
            
            for user in users:
                if not user.get('face_embedding'):
                    continue
                
                known_embedding = np.array(user['face_embedding'])
                
                # Normalize for cosine similarity
                known_embedding = known_embedding / np.linalg.norm(known_embedding)
                
                # Calculate cosine similarity (dot product of normalized vectors)
                similarity = np.dot(current_embedding, known_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = user
            
            # Check threshold (cosine similarity: higher is better, typical threshold: 0.4-0.6)
            if best_similarity > self.recognition_threshold:
                print(colorama.Fore.GREEN + f"[FACE] ✅ Recognized: {best_match['username']} (similarity: {best_similarity:.3f})" + colorama.Style.RESET_ALL)
                return best_match
            else:
                print(colorama.Fore.YELLOW + f"[FACE] ❌ No match (best similarity: {best_similarity:.3f} < {self.recognition_threshold})" + colorama.Style.RESET_ALL)
                return None
                
        except Exception as e:
            print(colorama.Fore.RED + f"[FACE] Recognition error: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def register_new_user(self, username: str, full_name: str, image_bytes: bytes,
                         gender: str = 'other', birth_year: int = None, 
                         age: int = None, avatar_url: str = None) -> Optional[int]:
        """
        Đăng ký user mới vào database
        
        Returns:
            user_id nếu thành công, None nếu thất bại
        """
        if not self.database:
            print(colorama.Fore.RED + "[FACE] No database connected" + colorama.Style.RESET_ALL)
            return None
        
        try:
            # Extract face embedding
            embedding = self.extract_face_embedding(image_bytes)
            if embedding is None:
                print(colorama.Fore.RED + "[FACE] No face detected" + colorama.Style.RESET_ALL)
                return None
            
            # Save to database
            user_id = self.database.create_user(
                username=username,
                full_name=full_name,
                face_embedding=embedding,
                gender=gender,
                birth_year=birth_year,
                age=age,
                avatar_url=avatar_url
            )
            
            if user_id:
                print(colorama.Fore.GREEN + f"[FACE] ✅ Registered user: {username} (ID: {user_id})" + colorama.Style.RESET_ALL)
            
            return user_id
            
        except Exception as e:
            print(colorama.Fore.RED + f"[FACE] Registration error: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def detect_emotion(self, image_bytes: bytes) -> Optional[str]:
        """
        Phát hiện cảm xúc từ khuôn mặt
        
        Args:
            image_bytes: Ảnh từ webcam (JPEG bytes)
        
        Returns:
            Emotion string (happy, sad, angry, etc.)
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Analyze emotion
            result = DeepFace.analyze(
                img_path=img,
                actions=['emotion'],
                enforce_detection=False,
                silent=True
            )
            
            if result:
                emotion = result[0]['dominant_emotion']
                confidence = result[0]['emotion'][emotion]
                print(colorama.Fore.CYAN + f"[EMOTION] {emotion} ({confidence:.1f}%)" + colorama.Style.RESET_ALL)
                return emotion
            
            return None
            
        except Exception as e:
            print(colorama.Fore.YELLOW + f"[EMOTION] Detection error: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def analyze_frame(self, image_bytes: bytes) -> Dict:
        """
        Phân tích đầy đủ: Face Recognition + Emotion
        
        Returns:
            {
                'user': User dict or None,
                'is_new_user': bool,
                'emotion': 'happy' or None,
                'greeting': 'Hello John! You look cheerful today!'
            }
        """
        # Recognize user
        user = self.recognize_user(image_bytes)
        is_new_user = (user is None)
        
        # Detect emotion
        emotion = self.detect_emotion(image_bytes)
        
        # Build greeting
        greeting = ""
        if user:
            greeting = f"Welcome back, {user['full_name']}!"
            if emotion and emotion in self.emotion_responses:
                greeting += f" {self.emotion_responses[emotion]}"
        elif emotion and emotion in self.emotion_responses:
            greeting = self.emotion_responses[emotion]
        
        return {
            'user': user,
            'is_new_user': is_new_user,
            'emotion': emotion,
            'greeting': greeting
        }


# Test
if __name__ == "__main__":
    colorama.init()
    detector = FaceEmotionDetector()
    print("✅ Face + Emotion Detector initialized!")
