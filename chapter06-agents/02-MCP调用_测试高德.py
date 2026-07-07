import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
import os
import dotenv



async def main():
    # 1. 加载环境变量
    dotenv.load_dotenv(dotenv_path='../.env')
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY2")
    os.environ["OPENAI_BASE_URL"] = os.getenv("OPENAI_BASE_URL2")


    # 2. 初始化模型
    model = ChatOpenAI(
        # model='MiniMax-M2.5',
        model='qwen3.5-plus',
        temperature=0.6
    )

    # 3. 连接高德 MCP 并获取工具
    client = MultiServerMCPClient(
        {
            "amap": {
                "url": f"https://mcp.amap.com/sse?key={os.getenv('GAODE_API_KEY')}",
                "transport": "sse",
            }
        }
    )
    tools = await client.get_tools()

    # 4. 创建 Agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt='你是一个智能助手，可以调用高德地图工具来查询'
    )
    print(f"✅ 成功加载 {len(tools)} 个高德地图工具:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    # 5. ✅ 关键修正：使用 ainvoke 进行异步调用
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "根据IP是192.168.0.158查询所在的地理位置是哪？"}]
    })
    print(result['messages'][-1].content)

# 6. 在标准脚本中运行
if __name__ == "__main__":
    asyncio.run(main())