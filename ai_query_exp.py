from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain import hub
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
import json
import difflib
import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv(override=True)

# print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
# print(f"LANGCHAIN_API_KEY: {os.getenv('LANGCHAIN_API_KEY')}")

STANDARD_MODEL = "gemini-2.0-flash"
QUICK_MODEL = "gemini-2.0-flash"
REASONING_MODEL = "gemini-2.0-flash"

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
        GEMINI_MODEL = os.getenv('GEMINI', 'gemini-2.0-flash')
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
    
    def query(self, question: str) -> str:
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
        agent_input = {"messages": [{"role": "user", "content": question}]}
        response = []
        for step in self.agent_executor.stream(agent_input, stream_mode="values"):
            print("\nStep:", step["messages"][-1])
            response = step["messages"][-1]
        return response.content if hasattr(response, 'content') else str(response)

def main():
    # Example usage
    agent = QueryAgent()
    
    # Example questions
    questions = [
        # "What are the top 5 companies by revenue in 2024?",
        "Which industry has the highest average ROE in 2024?",
        # "Top 3 cong ty cong nghe lam an tot nhat ?",
        # "Top 3 nha banks lam an tot nhat ?",
        # "Toi co nen dau tu vao cong ty FPT hay khong ?",
        # "FPT lai nhieu ko ?" 
        # "FPT lãi ròng 10 năm gần đây ntn ?",
        # "FPT tỉ suất lãi ròng 10 năm gần đây ntn ?",
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        answer = agent.query(question)
        print(f"Answer: {answer}")

if __name__ == "__main__":
    main()
