from fastmcp import FastMCP
from langchain_community.tools import TavilySearchResults
import os
import dotenv
from fastmcp.prompts import PromptMessage
from mcp.types import TextContent

dotenv.load_dotenv(dotenv_path='../.env')
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")


mcp_server=FastMCP(name='my_MCP',instructions='使用Python代码实现的MCP服务器')

@mcp_server.tool(name='my')
def my_search(query:str)-> str | None:
    try:
        print('执行我的工具，输入的参数',query)
    except Exception as e:
        print(e)
        return '没有搜索到任何内容'

@mcp_server.tool()
def say_hello(username:str)->str:
    """给指定用户打个招呼"""
    return f'{username}，你好，今天天气不错！'


# 提示词模版
@mcp_server.prompt
def ask_about_topic(topic:str)->str:
    """生成请求解释特定主题的用户消息模版"""
    return f'能否请您解释一下{topic}这个概念'

# 高级提示模版：返回结构化消息对象
@mcp_server.prompt
def generate_code_request(language:str,task_description:str)->PromptMessage:
    """生成代码编写请求的用户消息模板"""
    content=f'请用{language}编写一个实现以下功能的函数:{task_description}'
    return PromptMessage(
        role='user',
        content=TextContent(type='text',text=content)
    )

# 结构化资源：自动序列化字典为JSON
@mcp_server.resource("resource://config")
def get_config()->dict:
    """以JSON格式返回应用配置"""
    return {
        "theme":"dark",       # 界面主题配置
        "version":'1.2.0',    # 当前版本号
        'features':['tools','resources'] # 已启动的功能模块
    }





