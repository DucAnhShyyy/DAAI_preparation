from fastapi import FastAPI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Optional
import os
import asyncio
import colorama
from colorama import Fore
from utils import *
from dotenv import load_dotenv


app = FastAPI()


load_dotenv()
GEMINI_MODEL = os.getenv('GEMINI', 'gemini-2.0-flash')
google_key = os.getenv("GOOGLE_API_KEY")
if not google_key:
    raise ValueError("Missing GOOGLE_API_KEY environment variable.")

OPEN_AI_MODELS = ["gpt-4o", "gpt-4o-mini", "o3-mini"]
ANTHROPIC_AI_MODELS = [
    os.getenv('CLAUDE_3_5_SONNET'),
    os.getenv('CLAUDE_3_5_HAIKU'),
    os.getenv('CLAUDE_3_7_SONNET'),
    os.getenv('CLAUDE_3_OPUS'),
    os.getenv('CLAUDE_3_HAIKU'),
]
TOOL_CALLING_MODEL = GEMINI_MODEL

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant."""
if not google_key:
    raise ValueError("Missing GOOGLE_API_KEY environment variable.")
class ToolsCallingAgentWithMem:
    def __init__(self, 
                 model_name: str = TOOL_CALLING_MODEL,
                 system_prompt: Optional[str] = None,
                 tools: Optional[List] = None):
        """Initialize the ToolsCallingAgentWithMem.
        
        Args:
            model_name: Name of the LLM model to use
            system_prompt: System prompt to use
            tools: List of tools to make available to the LLM
        """
        # Initialize the LLM
        if model_name == "gemini-2.0-flash":
            self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, google_api_key=google_key, credentials=None)
        elif model_name in OPEN_AI_MODELS:
            self.llm = ChatOpenAI(model=model_name)
        elif model_name in ANTHROPIC_AI_MODELS:
           self.llm = ChatAnthropic(model=model_name)
            
        # Set system prompt
        if system_prompt is None:
            system_prompt = DEFAULT_SYSTEM_PROMPT
            
        # Initialize message history
        self.messages = [SystemMessage(content=system_prompt)]
        
        # Set up tools
        self.tools = tools if tools is not None else []
        self.tools_map = {tool.name: tool for tool in self.tools}
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def reset(self):
        """Reset the conversation history."""
        system_prompt = self.messages[0].content
        self.messages = [SystemMessage(content=system_prompt)]

    async def process_user_message(self, user_message: str) -> str:
        """Process a user message and return the final response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            str: The final response from the LLM
        """
        # Add user message to history
        self.messages.append(HumanMessage(content=user_message))
        
        count_added_messages = 0
        # initial response from LLM
        response = self.llm_with_tools.invoke(self.messages)
        self.messages.append(response)
        count_added_messages += 1
        
        # Handle tool calls if any
        while response.tool_calls:
            for tool_call in response.tool_calls:
                # Execute the tool
                tool_name = tool_call['name'].lower()
                tool_selected = self.tools_map[tool_name]
                tool_result = tool_selected.invoke(tool_call)
                
                # Create tool message
                tool_content = str(tool_result)
                if hasattr(tool_result, 'to_dict'):  # Handle pandas DataFrame
                    tool_content = tool_result.to_string()
                elif isinstance(tool_result, (list, dict)):
                    tool_content = tool_result
                
                tool_message = ToolMessage(
                    content=tool_content,
                    tool_call_id=tool_call['id'],
                    name=tool_call['name']
                )
                
                self.messages.append(tool_message)
                count_added_messages += 1
            # Get next response
            response = self.llm_with_tools.invoke(self.messages)
            self.messages.append(response)
            count_added_messages += 1

        last_message = self.messages[-1]
        content = last_message.content

        # Remove all intermediate messages and add the final one
        for i in range(count_added_messages):
            self.messages.pop()
        self.messages.append(last_message)

        return content  # Return full response for display
agent = ToolsCallingAgentWithMem(model_name=TOOL_CALLING_MODEL, system_prompt=DEFAULT_SYSTEM_PROMPT, tools=SALE_TOOLS)

@app.get("/")
def root():
    return {"response": """
    Chào mừng bạn đến với Chatbot Rangdong!
    Nhập 'quit' hoặc 'exit' để thoát ra khỏi chương trình.
    Nhập 'reset' để bắt đàu cuộc trò chuyện mới
    """}

@app.post("/chat")
async def chat_endpoint(request: dict):
    global agent
    user_message = request.get("message", "")
    if not user_message:
        return {"error": "No message provided"}

    response = await agent.process_user_message(user_message)
    return {"response": response}

    