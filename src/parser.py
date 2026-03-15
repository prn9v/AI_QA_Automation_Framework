import json
import re

class TestCaseParser:
    """
    Parses raw AI output and extracts clean test case objects.
    AI output is messy — this class cleans it up.
    """
    
    def parse(self, raw_text: str) -> list[dict]:
        """
        Extract JSON from AI response.
        
        Args:
            raw_text: The raw string from AI
            
        Returns:
            List of test case dictionaries
        """
        # Try to find JSON array in the response
        json_match = re.search(r'\[[\s\S]*\]', raw_text)
        
        if not json_match:
            raise ValueError("AI response did not contain valid JSON test cases")
        
        json_str = json_match.group(0)
        test_cases = json.loads(json_str)
        
        # Validate and clean each test case
        cleaned = []
        for i, tc in enumerate(test_cases):
            cleaned.append({
                "id": tc.get("id", f"TC{i+1:03d}"),
                "title": tc.get("title", "Untitled Test"),
                "preconditions": tc.get("preconditions", "None"),
                "steps": tc.get("steps", []),
                "expected_result": tc.get("expected_result", ""),
                "priority": tc.get("priority", "Medium"),
                "test_type": tc.get("test_type", "Functional"),
                "status": "NOT RUN"
            })
        
        print(f"✅ Parsed {len(cleaned)} test cases successfully")
        return cleaned
    
    def save_to_json(self, test_cases: list[dict], filepath: str):
        """Save parsed test cases to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(test_cases, f, indent=2)
        print(f"💾 Saved test cases to {filepath}")