from fastapi import FastAPI, Body
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langgraph.prebuilt import create_react_agent
from langchain import hub
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import List, Optional
import json
import difflib
import os
import sys
from utils import *
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()


# Code 

GEMINI_MODELS = ["gemini-2.0-flash"]

OPEN_AI_MODELS = ["gpt-4o", "gpt-4o-mini", "o3-mini"]
ANTHROPIC_AI_MODELS = [
    os.getenv('CLAUDE_3_5_SONNET'),
    os.getenv('CLAUDE_3_5_HAIKU'),
    os.getenv('CLAUDE_3_7_SONNET'),
    os.getenv('CLAUDE_3_OPUS'),
    os.getenv('CLAUDE_3_HAIKU'),
]

STANDARD_MODEL = "gemini-2.0-flash"
QUICK_MODEL = "gemini-2.0-flash"
REASONING_MODEL = "gemini-2.0-flash"

DEFAULT_SYSTEM_PROMPT = """Bạn là một trợ lý hữu ích. Hãy luôn trả lời bằng tiếng Việt."""


class QueryAgent:
    def __init__(self):
        # Initialize database connection
        self.db = SQLDatabase.from_uri(
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
            f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
        )
        
        # Load templates
        with open("templates/sql_templates.json", "r", encoding="utf-8") as f:
            self.templates = json.load(f)

        # Initialize LLM
        # CLAUDE_3_5_SONNET = os.getenv('CLAUDE_3_5_SONNET')
        # Lấy model name từ biến môi trường, ví dụ: 'gemini-pro'
        GEMINI_MODEL = "gemini-2.0-flash"
        GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

        # Khởi tạo Gemini
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0
        )
        # Initialize SQL toolkit and get tools
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()
        
        # Load system prompt for the agent
        prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
        
        # Add custom instructions to the prompt template
        today = datetime.now().strftime("%Y-%m-%d")
        additional_instructions = f"""
        
        Additional Instructions:
        1. When dealing with financial ratios like ROE, ROA, or Net Income Margin (NIM), they are stored as percentages but in decimal form (E.g: 15% is stored as 0.15) in the database.
        2. Format your responses with appropriate units (Bn. VND for money, % for ratios).
        3. Khi user hỏi về 1 ngành nào đó, tên ngành chưa chắc đúng, tìm và match với ngành gần nhất trong bảng vn100_listing_by_industry
        4. Các câu hỏi về "top" cần trả vể kết quả unique (ví dụ: "Top 3 công ty có lợi nhuận cao nhất" phải trả về 3 công ty, không được trả về 1 công ty)
        Today is (YYYY-MM-DD): {today}
        Your final answer should be in Vietnamese.
        """ 
        
        system_message = prompt_template.format(dialect="MySQL", top_k=5) + additional_instructions
        
        # Create ReAct agent
        self.agent_executor = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_message
        )

    def match_template(self, question: str):
        """Return SQL if user question closely matches a predefined template"""
        questions = [t['question'] for t in self.templates]
        match = difflib.get_close_matches(question.strip(), questions, n=1, cutoff=0.85)
        if match:
            for t in self.templates:
                if t["question"] == match[0]:
                    return t["sql"]
        return None
    
    def query(self, question: str, history: Optional[List[dict]] = None) -> str:
        """Template-based if match, else fallback to LLM"""
        matched_sql = self.match_template(question)
        if matched_sql:
            print(f"\n⚡ Using template for: {question}")
            try:
                result = self.db.run(matched_sql)
                return f"[Kết quả từ template SQL]\n{result}"
            except Exception as e:
                return f"⚠️ Lỗi khi chạy SQL template: {str(e)}"
        
        print(f"\n🤖 Using LLM for: {question}")
        agent_input = {"messages": history + [{"role": "user", "content": question}] if history else [{"role": "user", "content": question}]}
        response = []
        for step in self.agent_executor.stream(agent_input, stream_mode="values"):
            print("\nStep:", step["messages"][-1])
            response = step["messages"][-1]
        return response.content if hasattr(response, 'content') else str(response)

agent = QueryAgent()

@app.get("/")
def root():
    return {"response": """
    Chào mừng bạn đến với Chatbot Rangdong!
    Nhập 'quit' hoặc 'exit' để thoát ra khỏi chương trình.
    Nhập 'reset' để bắt đàu cuộc trò chuyện mới
    """}

@app.post("/chat")
async def chat_endpoint(request: dict = Body(..., examples={"message": "Xin chào. Bạn có thể làm gì?"})):
    global agent
    user_message = request.get("message", "")
    history = request.get("history",[])
    if not user_message:
        return {"error": "Không có tin nhắn."}

    response = agent.query(user_message, history)
    return {"response": response}

    