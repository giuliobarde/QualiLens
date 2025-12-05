"""
OpenAI client for language model operations using LangChain.

This module provides a unified interface for OpenAI operations including
embeddings, completions, and other language model tasks using LangChain.
Supports both synchronous and asynchronous operations for parallel processing.
"""

import logging
from typing import List, Optional, Dict, Any
import os
import asyncio
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage

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
    
    def generate_completion(self, prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 1000, temperature: float = 0.0) -> Optional[str]:
        """
        Generate text completion using OpenAI models.

        Args:
            prompt (str): Input prompt
            model (str): OpenAI model to use
            max_tokens (int): Maximum tokens to generate
            temperature (float): Sampling temperature (0.0 = deterministic, 1.0 = creative). Default 0.0 for consistency.

        Returns:
            Optional[str]: Generated text or None if failed
        """
        try:
            # Create chat model instance with specific parameters
            chat_model = ChatOpenAI(
                openai_api_key=self.api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature  # Add temperature for deterministic scoring
            )

            messages = [HumanMessage(content=prompt)]
            response = chat_model.invoke(messages)

            completion = response.content
            logger.info(f"Generated completion using model: {model} (temperature={temperature})")
            return completion

        except Exception as e:
            logger.error(f"Failed to generate completion: {str(e)}")
            return None
    
    async def generate_completion_async(self, prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 1000, temperature: float = 0.0) -> Optional[str]:
        """
        Generate text completion asynchronously using OpenAI models.
        This allows parallel execution of multiple LLM calls.

        Args:
            prompt (str): Input prompt
            model (str): OpenAI model to use
            max_tokens (int): Maximum tokens to generate
            temperature (float): Sampling temperature (0.0 = deterministic, 1.0 = creative). Default 0.0 for consistency.

        Returns:
            Optional[str]: Generated text or None if failed
        """
        try:
            # Create chat model instance with specific parameters
            chat_model = ChatOpenAI(
                openai_api_key=self.api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )

            messages = [HumanMessage(content=prompt)]
            # Use async invoke for non-blocking execution
            response = await chat_model.ainvoke(messages)

            completion = response.content
            logger.info(f"Generated async completion using model: {model} (temperature={temperature})")
            return completion

        except Exception as e:
            logger.error(f"Failed to generate async completion: {str(e)}")
            return None
    
    async def generate_completions_parallel(self, prompts: List[Dict[str, Any]]) -> List[Optional[str]]:
        """
        Generate multiple completions in parallel.
        
        Args:
            prompts: List of dicts with keys: 'prompt', 'model' (optional), 'max_tokens' (optional), 'temperature' (optional)
        
        Returns:
            List of completion strings (or None for failed calls)
        """
        tasks = []
        for prompt_config in prompts:
            prompt = prompt_config.get('prompt', '')
            model = prompt_config.get('model', 'gpt-4o-mini')
            max_tokens = prompt_config.get('max_tokens', 1000)
            temperature = prompt_config.get('temperature', 0.0)
            
            task = self.generate_completion_async(prompt, model, max_tokens, temperature)
            tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        completions = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Parallel completion failed: {str(result)}")
                completions.append(None)
            else:
                completions.append(result)
        
        logger.info(f"Completed {len(completions)} parallel LLM calls")
        return completions
    