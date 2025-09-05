import os
import requests
import logging
from textblob import TextBlob

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.hf_api_key = os.environ.get("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")
        # Use a reliable and available model for government services
        self.hf_api_url = "https://api-inference.huggingface.co/models/ibm-granite/granite-3.3-8b-instruct"
        
    def get_ai_response(self, question):
        """Get AI response from Hugging Face API with fallback to rule-based responses"""
        # Check if API key is available first
        if self.hf_api_key:
            try:
                # Format the question for better government service context
                formatted_question = f"As a government services assistant, please help with this question: {question}"
                
                headers = {"Authorization": f"Bearer {self.hf_api_key}"}
                payload = {
                    "inputs": formatted_question,
                    "parameters": {
                        "max_length": 200,
                        "temperature": 0.7,
                        "do_sample": True
                    }
                }
                
                response = requests.post(self.hf_api_url, headers=headers, json=payload, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "").strip()
                        # Clean up the response - remove the original question if it's repeated
                        if formatted_question in generated_text:
                            generated_text = generated_text.replace(formatted_question, "").strip()
                        if generated_text and len(generated_text) > 10:
                            return generated_text
                elif response.status_code == 503:
                    logger.info("Hugging Face model is loading, using fallback response")
                else:
                    logger.warning(f"Hugging Face API returned status {response.status_code}: {response.text}")
                    
            except Exception as e:
                logger.error(f"Error calling Hugging Face API: {e}")
        else:
            logger.info("No Hugging Face API key available, using rule-based responses")
        
        # Fallback to rule-based responses for government services
        return self._get_rule_based_response(question.lower())
    
    def _get_rule_based_response(self, question_lower):
        """Provide rule-based responses for common government service questions"""
        
        # Government services knowledge base
        if any(word in question_lower for word in ['license', 'permit', 'driving']):
            return """For driver's license services, you can:
• Renew your license online through your state's DMV website
• Apply for a new license at your local DMV office
• Required documents typically include proof of identity, residency, and Social Security
• Most renewals can be completed online if you meet eligibility requirements
• Check your state's specific requirements as they may vary"""
            
        elif any(word in question_lower for word in ['vote', 'voting', 'election']):
            return """For voting information:
• Register to vote through your state's election website or local election office
• Check your voter registration status online
• Find your polling location using your state's voter portal
• Request absentee or mail-in ballots if available in your state
• Early voting options vary by state - check local requirements
• Bring valid ID to vote (requirements vary by state)"""
            
        elif any(word in question_lower for word in ['tax', 'taxes', 'irs']):
            return """For tax-related services:
• File federal taxes through IRS.gov or approved tax software
• State tax filing requirements vary - check your state's revenue website
• Get tax transcripts and forms from IRS.gov
• Set up payment plans for tax debt through IRS online services
• Free tax preparation assistance available through VITA programs
• Tax deadline is typically April 15th (unless extended)"""
            
        elif any(word in question_lower for word in ['benefit', 'benefits', 'social security', 'medicare']):
            return """For government benefits:
• Apply for Social Security benefits at ssa.gov
• Medicare enrollment typically begins 3 months before turning 65
• SNAP (food assistance) applications through your state's social services
• Unemployment benefits through your state's labor department
• Medicaid applications through your state's health department
• Veterans benefits through va.gov
• Check eligibility requirements for each program"""
            
        elif any(word in question_lower for word in ['passport', 'travel']):
            return """For passport and travel services:
• Apply for passports at passport acceptance facilities or by mail
• Passport cards available for land/sea travel to Canada, Mexico, Caribbean
• Expedited processing available for additional fees
• Required documents include citizenship proof and photo ID
• Passport photos must meet specific requirements
• Check current processing times on travel.state.gov"""
            
        elif any(word in question_lower for word in ['court', 'legal', 'lawyer']):
            return """For legal assistance:
• Find legal aid services through your state's bar association
• Small claims court for disputes under state-specific dollar limits
• Public defender services for criminal cases if you qualify
• Legal self-help resources available through court websites
• Mediation services often available for civil disputes
• Contact your local courthouse for specific procedures"""
            
        else:
            return """I'm here to help with government services! I can provide information about:
• Driver's licenses and permits
• Voting and elections
• Tax filing and payments
• Government benefits (Social Security, Medicare, SNAP, etc.)
• Passport and travel documents
• Legal services and court procedures
• Business licenses and permits

Please ask me about any specific government service you need help with, and I'll provide detailed guidance."""

    def analyze_sentiment(self, text):
        """Analyze sentiment of feedback text using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return "positive"
            elif polarity < -0.1:
                return "negative"
            else:
                return "neutral"
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "neutral"

# Create global instance
ai_service = AIService()
