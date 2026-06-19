import asyncio

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from llm.my_llm import model


python_mcp_server_config={
    'url':'http://127.0.0.1:8888/sse',
    'transport':'sse'
}
mcp_client = MultiServerMCPClient({
    'my_mcp':python_mcp_server_config
})

async def create_mcp():
    """必须是异步函数"""
    mcp_tools=await mcp_client.get_tools()
    print(f'拿到所有的工具{mcp_tools}')
    p=await mcp_client.get_prompt(server_name='my_mcp',prompt_name='ask_about_topic',
                                   arguments={'topic':'深度学习'})
    print(f'拿到的提示词模版{p}')
    r=await mcp_client.get_resources(server_name='my_mcp',uris=['resource://config'])
    print(f'拿到的结构化资源{r}')


    return create_agent(
        model=model,
        tools=mcp_tools,
        system_prompt='你是一个AI助手，尽可能的调用工具回答用户的问题'
    )

if __name__ == '__main__':
    agent = asyncio.run(create_mcp())





