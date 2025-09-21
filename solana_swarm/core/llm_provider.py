"""
LLM Provider Implementation for Solana Swarm Intelligence
Uses OpenRouter API for diverse model access
"""

import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging
import json
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: str = "openrouter"
    api_key: str = ""
    model: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_url: str = "https://openrouter.ai/api/v1"
    system_prompt: Optional[str] = None

    def validate(self) -> None:
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.model:
            raise ValueError("Model name is required")
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")
        if self.max_tokens < 1:
            raise ValueError("Max tokens must be positive")

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self):
        self._session = None
    
    @abstractmethod
    async def query(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        expect_json: bool = False
    ) -> str:
        """Query the LLM with a prompt"""
        pass

    @abstractmethod
    async def batch_query(
        self,
        prompts: List[str],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> List[str]:
        """Query the LLM with multiple prompts"""
        pass

    async def close(self) -> None:
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()

class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider implementation"""

    def __init__(self, config: LLMConfig):
        """Initialize OpenRouter provider"""
        super().__init__()
        self.config = config
        self.config.validate()

    async def _ensure_session(self):
        """Ensure HTTP session exists"""
        if not self._session or self._session.closed:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://solana-agent-studio.com",
                "X-Title": "Solana AI Agent Studio"
            }
            self._session = aiohttp.ClientSession(headers=headers)

    async def query(
        self, 
        prompt: str, 
        temperature: Optional[float] = None, 
        max_tokens: Optional[int] = None,
        expect_json: bool = False
    ) -> str:
        """Query the LLM provider with a prompt."""
        try:
            await self._ensure_session()
            
            messages = []
            if self.config.system_prompt:
                messages.append({"role": "system", "content": self.config.system_prompt})
            
            if expect_json:
                prompt += "\\n\\nRespond with valid JSON only."
            
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens
            }
            
            async with self._session.post(
                f"{self.config.api_url}/chat/completions",
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
                
                if expect_json:
                    try:
                        # Validate JSON
                        json.loads(content)
                        return content
                    except json.JSONDecodeError:
                        # Extract JSON from response if wrapped in text
                        import re
                        json_match = re.search(r'\\{.*\\}', content, re.DOTALL)
                        if json_match:
                            return json_match.group()
                        raise ValueError("Expected JSON response but got invalid JSON")
                
                return content.strip()

        except Exception as e:
            logger.error(f"Error querying OpenRouter API: {str(e)}")
            raise

    async def batch_query(
        self,
        prompts: List[str],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> List[str]:
        """Query with multiple prompts in parallel."""
        try:
            results = []
            for prompt in prompts:
                result = await self.query(prompt, temperature=temperature, max_tokens=max_tokens)
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Error in batch query: {str(e)}")
            raise

def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Create LLM provider instance based on configuration."""
    config.validate()
    provider = config.provider.lower().strip()
    
    if provider in ["openrouter", "or"]:
        return OpenRouterProvider(config)
    
    raise ValueError(f"Unsupported LLM provider '{provider}'. Currently supported: openrouter")