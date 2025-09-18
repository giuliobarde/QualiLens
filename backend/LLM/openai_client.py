"""
OpenAI client for language model operations using LangChain.

This module provides a unified interface for OpenAI operations including
embeddings, completions, and other language model tasks using LangChain.
"""

import logging
from typing import List, Optional, Dict, Any
import os
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Unified OpenAI client for various language model operations using LangChain.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key (Optional[str]): OpenAI API key (defaults to environment variable)
            
        Raises:
            ValueError: If API key is not provided
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize LangChain components
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        self.chat_model = ChatOpenAI(openai_api_key=self.api_key)
        logger.info("OpenAI client initialized successfully with LangChain")
    
    def generate_completion(self, prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 1000) -> Optional[str]:
        """
        Generate text completion using OpenAI models.
        
        Args:
            prompt (str): Input prompt
            model (str): OpenAI model to use
            max_tokens (int): Maximum tokens to generate
            
        Returns:
            Optional[str]: Generated text or None if failed
        """
        try:
            # Create chat model instance with specific parameters
            chat_model = ChatOpenAI(
                openai_api_key=self.api_key,
                model=model,
                max_tokens=max_tokens
            )
            
            messages = [HumanMessage(content=prompt)]
            response = chat_model.invoke(messages)
            
            completion = response.content
            logger.info(f"Generated completion using model: {model}")
            return completion
            
        except Exception as e:
            logger.error(f"Failed to generate completion: {str(e)}")
            return None
    