import requests
import json
from typing import Dict, Any, List, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://192.168.1.90:11434"):
        self.base_url = base_url
        self.available_models = self.get_available_models()
    
    def get_available_models(self) -> List[str]:
        """Fetch available models from Ollama server"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                return [model['name'] for model in models['models']] if 'models' in models else []
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama server: {str(e)}")
            return []
        except Exception as e:
            print(f"Error fetching models: {str(e)}")
            return []
    
    def generate_analysis(self, prompt: str, model: str = "llama2") -> Optional[str]:
        """Generate analysis using specified Ollama model"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            return None
        except requests.exceptions.Timeout:
            print("Analysis request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama server: {str(e)}")
            return None
        except Exception as e:
            print(f"Error generating analysis: {str(e)}")
            return None
    
    def analyze_test_points(self, test_point_data: Dict[str, Any], model: str = "llama2") -> Optional[str]:
        """Analyze test point data using AI model"""
        total = test_point_data.get('total', 0)
        valid = test_point_data.get('valid', 0)
        top = test_point_data.get('top_accessible', 0)
        bottom = test_point_data.get('bottom_accessible', 0)
        
        coverage_percent = (valid / total * 100) if total > 0 else 0
        
        prompt = f"""
        Analyze this PCB test point data as a test engineering expert:

        Statistics:
        - Total Test Points: {total}
        - Valid Test Points: {valid} ({coverage_percent:.1f}% coverage)
        - Top Side Accessible: {top}
        - Bottom Side Accessible: {bottom}

        Provide a concise analysis covering:
        1. Test Coverage Assessment
        2. Key Recommendations
        3. Critical Issues
        4. Fixture Design Guidelines

        Format the response with clear headers and bullet points.
        Keep the analysis focused and actionable.
        """
        
        analysis = self.generate_analysis(prompt, model)
        if analysis:
            # Clean up and format the response
            analysis = analysis.replace('\n\n\n', '\n\n')  # Remove extra newlines
            analysis = analysis.strip()
            
            # Add Streamlit-compatible formatting
            analysis = f"""
            ### Test Point Analysis Results

            {analysis}
            
            ---
            *Analysis generated using {model}*
            """
            
            return analysis
        return None