# extraction/llm_client.py
import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger("llm_client")

class LLMClient:
    """
    Client for interacting with LLM APIs (OpenAI, Anthropic, etc.)
    """
    def __init__(self, provider="openai", api_key=None, model=None):
        """
        Initialize the LLM client
        
        Args:
            provider: The LLM provider ("openai", "anthropic", etc.)
            api_key: API key for the provider (if None, will look for environment variable)
            model: The model to use (if None, will use default)
        """
        self.provider = provider.lower()
        
        # Set API key
        if api_key:
            self.api_key = api_key
        else:
            if provider == "openai":
                self.api_key = os.environ.get("OPENAI_API_KEY")
            elif provider == "anthropic":
                self.api_key = os.environ.get("ANTHROPIC_API_KEY")
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        if not self.api_key:
            logger.warning(f"No API key found for {provider}. LLM extraction will not work.")
        
        # Set default model based on provider
        if not model:
            if provider == "openai":
                self.model = "gpt-4o"
            elif provider == "anthropic":
                self.model = "claude-3-opus-20240229"
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        else:
            self.model = model
            
        logger.info(f"Initialized LLM client with provider {provider} and model {self.model}")
    
    def extract_from_text(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from text using the LLM
        
        Args:
            text: The text to extract from
            schema: Dictionary describing the fields to extract
            
        Returns:
            Dictionary of extracted fields
        """
        if not self.api_key:
            logger.error("Cannot extract: No API key configured")
            return {}
            
        # Format the schema for the prompt
        schema_str = json.dumps(schema, indent=2)
        
        # Create the prompt
        prompt = f"""
        Extract the following information from the document text provided below.
        Return the data in a valid JSON format that matches this schema:
        
        {schema_str}
        
        For any fields you cannot find in the document, use null.
        For numerical values, return numbers without currency symbols.
        For dates, normalize to YYYY-MM-DD format if possible.
        
        Document text:
        {text}
        """
        
        try:
            # Call the appropriate LLM API
            if self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "anthropic":
                return self._call_anthropic(prompt)
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return {}
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return {}
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """
        Call the OpenAI API
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Parsed response as a dictionary
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document extraction assistant. Extract the requested information from the document and return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {}
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """
        Call the Anthropic API
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Parsed response as a dictionary
        """
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model,
                max_tokens=4096,
                system="You are a document extraction assistant. Extract the requested information from the document and return only valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Try to extract JSON from the response
            content = response.content[0].text
            # Find JSON in the content (Claude may wrap it in ```)
            import re
            json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                return json.loads(content)
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return {}