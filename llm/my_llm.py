import os
import dotenv
from langchain.chat_models import init_chat_model
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI

# 定义的模型类
dotenv.load_dotenv(dotenv_path='../.env')
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY2")
os.environ["OPENAI_BASE_URL"] = os.getenv("OPENAI_BASE_URL2")



# ================== 2. 初始化模型和工具 ==================
model = init_chat_model(
    model='qwen3.6-flash-2026-04-16',
    temperature=0.6,
    model_provider='openai',
    profile={"max_input_tokens": 128_000}
    # 开启深度思考
    # extra_body={"enable_thinking": True},
    # 启用联网搜索功能
    # extra_body={"enable_search": True},
)

model_tool = ChatOpenAI(
    model="qwen3.6-flash-2026-04-16",
    temperature=0.6,
    # extra_body={"enable_thinking": False},

    # max_tokens=128_000
)





