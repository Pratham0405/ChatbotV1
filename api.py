import os
import base64
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider, ClientSecretCredential
import json
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import traceback

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Azure OpenAI Chat API",
    description="API for interacting with Azure OpenAI's chat models",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    user_message: str
    system_message: Optional[str] = None
    max_tokens: Optional[int] = 800
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    frequency_penalty: Optional[float] = 0
    presence_penalty: Optional[float] = 0
    stop: Optional[list] = None
    stream: Optional[bool] = False

class ChatAPI:
    def __init__(self):
        """Initialize the ChatAPI with environment variables"""
        # Required configuration - will raise error if not set
        self.endpoint = self._get_required_env("AZURE_OPENAI_ENDPOINT")
        self.deployment = self._get_required_env("AZURE_OPENAI_DEPLOYMENT_NAME")
        
        # Optional configuration with defaults
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        
        # Initialize client
        self.client = self._initialize_client()
    
    def _get_required_env(self, var_name: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Missing required environment variable: {var_name}")
        return value
    
    def _initialize_client(self) -> AzureOpenAI:
        """Initialize Azure OpenAI client with Entra ID authentication"""
        try:
            # Get credentials from environment variables
            tenant_id = self._get_required_env("AZURE_TENANT_ID")
            client_id = self._get_required_env("AZURE_CLIENT_ID")
            client_secret = self._get_required_env("AZURE_CLIENT_SECRET")
            
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            token_provider = get_bearer_token_provider(
                credential, 
                "https://cognitiveservices.azure.com/.default"
            )
                
            return AzureOpenAI(
                azure_endpoint=self.endpoint,
                azure_ad_token_provider=token_provider,
                api_version=self.api_version,
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Azure OpenAI client: {str(e)}")
    
    def create_chat_completion(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Create a chat completion with optional parameters
        
        Args:
            user_message: The user's message content
            system_message: Optional system prompt message
            **kwargs: Additional parameters for completion
            
        Returns:
            dict: The completion response or error message
        """
        try:
            messages = self._build_messages(user_message, system_message)
            
            params = {
                "model": self.deployment,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 800),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.95),
                "frequency_penalty": kwargs.get("frequency_penalty", 0),
                "presence_penalty": kwargs.get("presence_penalty", 0),
                "stop": kwargs.get("stop"),
                "stream": kwargs.get("stream", False),
            }
            
            completion = self.client.chat.completions.create(**params)
            return json.loads(completion.choices.message.content.to_json())
            
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}
    
    def _build_messages(self, user_message: str, system_message: Optional[str]) -> list:
        """Build the messages list for the API call"""
        messages = []
        
        if system_message:
            messages.append({
                "role": "system",
                "content": [{"type": "text", "text": system_message}]
            })
        else:
            messages.append({
                "role": "system",
                "content": [{"type": "text", "text": "You are an AI assistant that helps people find information."}]
            })
            
        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": user_message}]
        })
        
        return messages

# Initialize ChatAPI instance
chat_api = ChatAPI()

@app.post("/chat")
async def chat_endpoint(chat_request: ChatRequest):
    """
    Endpoint for chat completions with Azure OpenAI
    
    Parameters:
    - user_message: The message from the user
    - system_message: Optional system message to guide the assistant's behavior
    - Other optional parameters to control the completion
    
    Returns:
    - The completion response from Azure OpenAI
    """
    try:
        response = chat_api.create_chat_completion(
            user_message=chat_request.user_message,
            system_message=chat_request.system_message,
            max_tokens=chat_request.max_tokens,
            temperature=chat_request.temperature,
            top_p=chat_request.top_p,
            frequency_penalty=chat_request.frequency_penalty,
            presence_penalty=chat_request.presence_penalty,
            stop=chat_request.stop,
            stream=chat_request.stream
        )
        
        if "error" in response:
            raise HTTPException(status_code=500, detail=response)
        
        return response.completion.choices[0].message.content if response.completion.choices else {"message": "No content returned"}
        # return JSONResponse(content=response)
        
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
