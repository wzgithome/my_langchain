# LangChain 学习笔记

从零开始学习 LangChain 的完整学习路径，涵盖从基础模型调用到构建 AI Agent 的全过程。

---

## 学习路线

```
模型调用 → 提示词工程 → Chain 链 → Memory 记忆 → Tools 工具 → Agents 智能体 → RAG 检索增强生成 → 实战项目
```

---

## 目录说明

| 章节 | 主题 | 内容概要 |
|------|------|----------|
| **chapter02** | Model IO | 模型调用、PromptTemplate、ChatPromptTemplate、FewShotPrompt、输出解析器 |
| **chapter03** | Chains | LCEL 语法理解、传统 Chain 用法、基于 LCEL 构建链 |
| **chapter04** | Memory | ConversationBufferMemory、ConversationSummaryMemory 等记忆模块 |
| **chapter05** | Tools | 自定义工具定义、大模型分析并调用工具、MCP 服务端实现 |
| **chapter06** | Agents | Agent 工具调用、MCP 协议实践（高德地图集成） |
| **chapter07** | RAG | 文档加载、文本拆分、Embedding、Chroma 向量数据库、检索器、智能对话助手综合案例 |
| **llm** | 共享模块 | 统一的 LLM 模型配置，供各章节复用 |

---

## 项目结构

```
AiProject/
├── .env                          # API 密钥配置（项目根目录）
├── llm/
│   ├── __init__.py
│   └── my_llm.py                 # 共享 LLM 模型配置（qwen3.6-flash）
├── chapter02-model IO/
│   ├── 01-模型调用.ipynb
│   ├── 02-模型调用.ipynb
│   ├── 03-提示词模版之PromptTemplate.ipynb
│   ├── 04-提示词模版之ChatPromptTemplate.ipynb
│   ├── 05-提示词模版之少量示例的提示词模版.ipynb
│   ├── 06-从文档中加载Prompt.ipynb
│   ├── 07-输出解析器的使用.ipynb
│   ├── 08-LangChain调用本地大模型.ipynb
│   ├── prompt.json
│   └── prompt.yaml
├── chapter03-chains/
│   ├── 01-LCEL语法的理解.ipynb
│   ├── 02-传统的Chain的使用.ipynb
│   └── 03-基于LCEL语法对新型的Chain.ipynb
├── chapter04-memory/
│   ├── 01-使用Memory模块之前.ipynb
│   ├── 02-基础Memory的使用.ipynb
│   └── 03-其他Memory的使用.ipynb
├── chapter05-tools/
│   ├── 01-自定义工具.ipynb
│   ├── 02-大模型分析工具的调用.ipynb
│   ├── tools_mcp_server.py       # FastMCP 服务端（工具 + 提示词 + 资源）
│   ├── tools_mcp_client.py       # MCP 客户端
│   ├── start_sse_server.py       # SSE 协议启动脚本
│   └── start_streamable_server.py # Streamable HTTP 协议启动脚本
├── chapter06-agents/
│   ├── 01-调用工具.ipynb
│   ├── 02-MCP调用_测试高德.py    # 高德地图 MCP 集成示例
│   ├── 03-MCP_server.py          # 简单 MCP 服务端
│   └── 04-MCP_client.py          # stdio 协议 MCP 客户端
└── chapter07-RAG/
    ├── 01-文档加载器的使用.ipynb
    ├── 02-文档拆分器的使用.ipynb
    ├── 03-文档嵌入模型的使用.ipynb
    ├── 04-向量数据库的使用.ipynb
    ├── 05-检索器的使用.ipynb
    ├── 06-综合案例：智能对话助手.ipynb
    ├── 复习.txt
    └── asset/load/               # RAG 示例文档
```

---

## 快速开始

### 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd AiProject

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install langchain langchain-openai openai tavily-python requests python-dotenv mcp langchain-tavily chromadb
```

### 配置 API 密钥

在项目根目录创建 `.env` 文件：

```bash
# OpenAI 兼容接口（示例使用 DashScope）
OPENAI_API_KEY2=your_api_key_here
OPENAI_BASE_URL2=https://dashscope.aliyuncs.com/compatible-mode/v1

# Tavily 搜索 API
TAVILY_API_KEY=your_tavily_api_key

# 高德地图 API（MCP 集成用）
GAODE_API_KEY=your_gaode_key_here
```

---

## 重点章节

### chapter02 - 模型 IO

学习 LangChain 的核心抽象：如何调用大模型、如何构造提示词、如何解析输出。

- `01/02` 模型调用（ChatOpenAI 基础用法）
- `03` PromptTemplate — 变量化提示词
- `04` ChatPromptTemplate — 多角色对话模板
- `05` FewShotPromptTemplate — 少量示例提示词
- `06` 从文件加载 Prompt（JSON/YAML）
- `07` 输出解析器（StrOutputParser、JsonOutputParser 等）
- `08` 调用本地大模型

### chapter03 - Chain 链

掌握 LCEL（LangChain Expression Language）的管道语法：

```python
chain = prompt | model | parser
result = chain.invoke({"input": "..."})
```

### chapter05 - Tools & MCP Server

- 自定义工具的两种方式：`@tool` 装饰器和 `StructuredTool`
- 使用 FastMCP 构建 MCP 服务端，暴露工具、提示词模板和结构化资源
- 支持 SSE 和 Streamable HTTP 两种传输协议

### chapter06 - Agents & MCP

- 通过 Notebook 学习 Agent 的工具调用机制
- MCP 客户端实践：连接高德地图 MCP 服务，实现地理位置查询
- stdio 协议的 MCP 客户端/服务端通信

### chapter07 - RAG

完整的 RAG 流程实践：

```
文档加载 → 文本拆分 → 向量嵌入 → 存入 Chroma → 检索 → 生成回答
```

---

## 技术栈

- **Python** 3.14
- **LangChain** — LLM 应用开发框架
- **OpenAI SDK** — 兼容 OpenAI 接口的大模型调用
- **DashScope** — 阿里云大模型服务（qwen3.6-flash）
- **Tavily** — 搜索引擎 API
- **Chroma** — 向量数据库
- **MCP** — Model Context Protocol（工具协议）
- **FastMCP** — MCP 服务端快速开发框架
- **Jupyter Notebook** — 学习和实验环境

---

## 学习资源

- [LangChain 官方文档](https://python.langchain.com/)
- [LangChain 中文教程](https://github.com/langchain-ai/langchain)
- [Tavily Search API](https://docs.tavily.com/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference/)
- [DashScope 文档](https://help.aliyun.com/zh/dashscope/)