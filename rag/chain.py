import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from typing import List, Dict, Any, Optional
from groq import Groq
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

class RAGChain:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        """
        Initializes the RAG chain with Groq API.
        Ensure GROQ_API_KEY is set in environment variables.
        """
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("Warning: GROQ_API_KEY not found in environment variables.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client. Error: {e}")
                self.client = None
                
        self.model_name = model_name

        # Template for Health Insight
        self.health_insight_prompt = PromptTemplate.from_template(
            """
            You are an expert AI Medical Assistant analysing a Digital Health Twin.
            
            CONTEXT FROM PATIENT RECORDS:
            {context}
            
            USER QUESTION: 
            {question}
            
            INSTRUCTIONS:
            1. Answer the question based ONLY on the provided context.
            2. If the answer is not in the context, say "I don't have enough data in the records."
            3. Provide a direct answer (Health Insight) and then explain which data points led to this (Reasoning).
            4. Be concise, professional, and empathetic.
            5. Do NOT provide medical advice.
            
            FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
            Health Insight: [Your direct answer here]
            Reasoning: [Explanation of which specific vitals, medications, or history were used]
            """
        )
        
    def generate_response(self, context_docs: List[Document], query: str) -> Dict[str, Any]:
        """
        Generates a response using Groq SDK and retrieved context.
        """
        if not self.client:
            return {
                "answer": "Groq client not initialized. Please checking GROQ_API_KEY.",
                "source_documents": context_docs
            }
            
        # Format context
        context_text = "\n\n".join([doc.page_content for doc in context_docs])
        
        # Format prompt
        prompt_text = self.health_insight_prompt.format(context=context_text, question=query)
        
        # Execute via SDK
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt_text,
                    }
                ],
                model=self.model_name,
            )
            response_text = chat_completion.choices[0].message.content
        except Exception as e:
            response_text = f"Error generating response from Groq: {str(e)}"
            
        return {
            "answer": response_text,
            "source_documents": context_docs
        }
