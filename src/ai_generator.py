import os
import requests
from dotenv import load_dotenv

load_dotenv()

class AITestGenerator:
    """
    Connects to Hugging Face Router API to generate test cases.
    Uses Llama-3.1-8B via Cerebras provider (fast + free tier).
    """
    
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # ✅ FIXED: Real model + real provider name (no :auto)
        # Cerebras is fastest and works on free tier
        self.model = "meta-llama/Llama-3.1-8B-Instruct:cerebras"
    
    def generate_test_cases(self, feature_description: str, num_cases: int = 5) -> str:
        prompt = self._build_prompt(feature_description, num_cases)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior QA engineer. Always respond with valid JSON only. No extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.5
        }
        
        print(f"🤖 Generating {num_cases} test cases for: {feature_description}")
        print(f"📡 Using model: {self.model}")
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            print("✅ AI response received!")
            return content
        else:
            # Print full error so we can debug
            print(f"❌ Full error response: {response.text}")
            raise Exception(f"API Error {response.status_code}: {response.text}")
    
    def _build_prompt(self, feature: str, num_cases: int) -> str:
        return f"""Generate exactly {num_cases} QA test cases for: {feature}

Respond with ONLY a valid JSON array. No markdown, no explanation, no code blocks.

[
  {{
    "id": "TC001",
    "title": "Verify successful login with valid credentials",
    "preconditions": "User account exists in the system",
    "steps": ["Navigate to login page", "Enter valid username", "Enter valid password", "Click Login button"],
    "expected_result": "User is redirected to dashboard",
    "priority": "High",
    "test_type": "Functional"
  }}
]

Now generate {num_cases} test cases for: {feature}"""