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
from sqlalchemy import create_engine, inspect
import re
# Load environment variables
load_dotenv(override=True)

STANDARD_MODEL = "gemini-2.0-flash"
QUICK_MODEL = "gemini-2.0-flash"
REASONING_MODEL = "gemini-2.0-flash"

class QueryAgent:
    def __init__(self):
        # Initialize database connection: Khởi tạo kết nối với Database
        self.db = SQLDatabase.from_uri(
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
            f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
        )

        # Load templates: file SQL query mẫu
        with open("templates/sql_templates.json", "r", encoding="utf-8") as f:
            self.templates = json.load(f)

        # Initialize LLM: mô hình ngôn ngữ lớn được dùng
        GEMINI_MODEL = os.getenv('GEMINI', 'gemini-2.0-flash')
        GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0
        )

        # Initialize SQL toolkit and get tools
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()

        # Load base system prompt: base prompt của langchain
        '''
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
        Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        You have access to tools for interacting with the database.
        Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

        To start you should ALWAYS look at the tables in the database to see what you can query.
        Do NOT skip this step.
        Then you should query the schema of the most relevant tables.
        '''
        prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
        today = datetime.now().strftime("%Y-%m-%d")
        additional_instructions = f"""
        Instructions:
        - Answer in Vietnamese.
        - The results are given without unit.
        - If asking for "Top" results, make sure N rows are unique.
        Today is {today}.
        """
        self.base_prompt_template = prompt_template.format(dialect="MySQL", top_k=5) + additional_instructions

        # Load schema.txt ONCE
        with open("schema.txt", "r", encoding="utf-8") as f:
            self.schema_text = f.read()

        self.agent_executor = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self.base_prompt_template
        )

    def generate_schema_file(self, output_file="schema.txt", sample_rows=3):
        """Generate schema.txt ONCE and save"""
        connection_uri = (
            f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
            f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
        )
        engine = create_engine(connection_uri)
        inspector = inspect(engine)

        schema_lines = []
        schema_lines.append("You are an expert at translating natural questions into SQL queries.\n")
        schema_lines.append("Database Schema:\n")

        with engine.connect() as conn:
            for table_name in inspector.get_table_names():
                schema_lines.append(f"Table: {table_name}")
                columns = inspector.get_columns(table_name)
                for col in columns:
                    name = col['name']
                    dtype = str(col['type'])
                    comment = col.get('comment', '')
                    line = f"- {name} ({dtype})"
                    if comment:
                        line += f": {comment}"
                    schema_lines.append(line)

                # Sample data
                try:
                    result = conn.execute(f"SELECT * FROM {table_name} LIMIT {sample_rows}")
                    rows = result.fetchall()
                    if rows:
                        headers = rows[0].keys()
                        schema_lines.append("Sample Data:")
                        schema_lines.append(", ".join(headers))
                        for row in rows:
                            row_data = ", ".join(str(v) for v in row.values())
                            schema_lines.append(row_data)
                except Exception as e:
                    print(f"⚠️ Warning: Cannot fetch sample data for {table_name}: {e}")

                schema_lines.append("")  # Blank line after each table

            # Foreign keys
            schema_lines.append("Foreign Key Relationships:")
            for table_name in inspector.get_table_names():
                fks = inspector.get_foreign_keys(table_name)
                for fk in fks:
                    referred_table = fk['referred_table']
                    constrained_columns = ', '.join(fk['constrained_columns'])
                    referred_columns = ', '.join(fk['referred_columns'])
                    schema_lines.append(f"- {table_name}.{constrained_columns} references {referred_table}.{referred_columns}")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(schema_lines))
        print(f"✅ Schema file saved to {output_file}")

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
        """Query by template if matched, else use LLM with static schema"""
        matched_sql = self.match_template(question)
        if matched_sql:
            print(f"\n⚡ Using template for: {question}")
            try:
                result = self.db.run(matched_sql)
                return f"[Kết quả từ template SQL]\n{result}"
            except Exception as e:
                return f"⚠️ Lỗi khi chạy SQL template: {str(e)}"
        
        print(f"\n🤖 Using LLM for: {question}")

        enriched_prompt = f"{self.schema_text}\n\nUser Question: {question}"

        agent_input = {"messages": [{"role": "user", "content": enriched_prompt}]}
        response = []
        for step in self.agent_executor.stream(agent_input, stream_mode="values"):
            print("\nStep:", step["messages"][-1])
            response = step["messages"][-1]
        
        # Parse nội dung trả về
        content = response.content if hasattr(response, 'content') else str(response)

        # Tìm SQL trong content
        sql_code = self.extract_sql(content)

        if sql_code:
            print(f"\n⚡ Running generated SQL:\n{sql_code}")
            try:
                result = self.db.run(sql_code)
                return f"[Kết quả từ LLM SQL]\n{result}"
            except Exception as e:
                return f"⚠️ Lỗi khi chạy SQL do LLM sinh ra: {str(e)}"
        else:
            return f"❗ Không tìm thấy SQL trong câu trả lời.\nNội dung: {content}"

    # Hàm tìm SQL trong nội dung trả về
    def extract_sql(self, text: str) -> str:
        """Try to extract SQL code from text"""
        # Cách đơn giản: tìm trong ```sql ... ``` block
        sql_blocks = re.findall(r"```sql(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        if sql_blocks:
            return sql_blocks[0].strip()
        
        # Nếu không có block, tìm lệnh SELECT/FROM
        sql_candidate = re.search(r"(SELECT .*?;)", text, flags=re.DOTALL | re.IGNORECASE)
        if sql_candidate:
            return sql_candidate.group(1).strip()

        return None

def main():
    agent = QueryAgent()

    # Nếu lần đầu tiên chưa có file schema.txt → uncomment dòng dưới:
    # agent.generate_schema_file()

    questions = [
        "Top 3 nhân viên có số kpi trung bình cao nhất quý 4 năm 2024?"
        # Thêm nhiều câu nếu muốn test
    ]

    for question in questions:
        print(f"\nQuestion: {question}")
        answer = agent.query(question)
        print(f"Answer: {answer}")

if __name__ == "__main__":
    main()