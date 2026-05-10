import os
import re
import sys
import dotenv
import requests
from openai import OpenAI
from tavily import TavilyClient

# ============================================================================
# 🔧 配置区域
# ============================================================================

# 系统提示词
AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。
- `get_transport(city: str)`: 查询城市交通指南（机场、火车站、地铁、打车等）。
- `get_restaurant(city: str, cuisine_type: str = "all")`: 推荐当地美食和餐厅。cuisine_type 可选: "all"(全品类), "local"(本地特色), "famous"(知名餐厅), "budget"(经济实惠), "high-end"(高端餐饮)。
- `estimate_budget(city: str, days: int, travel_style: str = "mid-range")`: 估算旅行预算。travel_style 可选: "budget"(经济型), "mid-range"(舒适型), "luxury"(豪华型)。
- `show_map(city: str, attractions: str)`: 查询景点的地理位置信息。attractions 为景点名称，多个景点用逗号分隔（如 "中山陵,夫子庙,玄武湖"）。
- `get_route(city: str, origin: str, destination: str, mode: str = "walk")`: 查询两个景点之间的路线。mode 可选: "walk"(步行), "drive"(驾车), "bus"(公交)，"subway"(地铁)。用户已在该城市，默认推荐地铁路线。默认返回时间最短的路线。地铁模式下优先推荐地铁方案。

# 支持的预设城市:
南京、上海、北京、广州、深圳、杭州、成都、重庆、武汉、西安

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对 Thought 和 Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action 的格式必须是以下之一:
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对 Thought-Action
- Action 必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束
- 可以结合对话历史记录进行推理
- 如果用户没有指定天数，默认3天；没有指定旅行风格，默认舒适型
- 推荐景点后，如果用户想查看地图位置，调用 show_map 展示

请开始吧!
"""

# 支持的城市列表
SUPPORTED_CITIES = [
    "南京", "上海", "北京", "广州", "深圳",
    "杭州", "成都", "重庆", "武汉", "西安"
]


# ============================================================================
# 🛠️ 工具函数定义
# ============================================================================

def get_weather(city: str) -> str:
    """
    通过调用 wttr.in API 查询真实的天气信息
    
    Args:
        city: 城市名称
        
    Returns:
        格式化后的天气描述
    """
    # API 端点，我们请求 JSON 格式的数据
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # 发起网络请求
        response = requests.get(url, timeout=10)
        # 检查响应状态码是否为 200
        response.raise_for_status()
        # 解析返回的 JSON 数据
        data = response.json()
        # 提取当前天气状况
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        # 格式化成自然语言返回
        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误：查询天气时遇到网络问题-{e}"
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"


def get_attraction(city: str, weather: str) -> str:
    """
    根据城市和天气，使用 Tavily Search API 搜索并返回优化后的景点推荐
    
    Args:
        city: 城市名称
        weather: 天气描述
        
    Returns:
        景点推荐内容
    """
    # 初始化 Tavily 客户端
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)

    # 构造一个精确的查询
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        # 调用 API，include_answer=True 会返回一个综合性的回答
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True
        )

        # Tavily 返回的结果已经非常干净，可以直接使用
        # response['answer'] 是一个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]

        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}:{result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的旅游景点推荐。"

        return "根据搜索，为您找到以下信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：执行 Tavily 搜索时出现问题-{e}"


def get_transport(city: str) -> str:
    """
    查询城市交通指南（机场、火车站、地铁、打车等）

    Args:
        city: 城市名称

    Returns:
        交通指南内容
    """
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)

    query = f"{city}交通指南 机场 火车站 地铁 出租车 网约车"

    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True
        )

        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}:{result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的交通信息。"

        return "根据搜索，为您找到以下交通信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：查询交通信息时出现问题-{e}"


def get_restaurant(city: str, cuisine_type: str = "all") -> str:
    """
    推荐当地特色美食和餐厅

    Args:
        city: 城市名称
        cuisine_type: 菜系类型（all/local/famous/budget/high-end）

    Returns:
        美食推荐内容
    """
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)

    type_map = {
        "all": "全品类美食推荐",
        "local": "本地特色小吃",
        "famous": "知名餐厅推荐",
        "budget": "经济实惠美食",
        "high-end": "高端餐饮推荐",
    }
    desc = type_map.get(cuisine_type, "全品类美食推荐")
    query = f"{city} {desc} 特色美食 餐厅推荐"

    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True
        )

        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}:{result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的美食推荐。"

        return "根据搜索，为您找到以下美食信息：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：查询美食信息时出现问题-{e}"


def estimate_budget(city: str, days: int = 3, travel_style: str = "mid-range") -> str:
    """
    估算旅行预算

    Args:
        city: 城市名称
        days: 旅行天数（默认3天）
        travel_style: 旅行风格（budget/mid-range/luxury）

    Returns:
        预算估算内容
    """
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = TavilyClient(api_key=api_key)

    style_map = {
        "budget": "经济型穷游",
        "mid-range": "舒适型",
        "luxury": "豪华型",
    }
    style_desc = style_map.get(travel_style, "舒适型")
    query = f"{city}{days}天{style_desc}旅行预算 住宿餐饮交通门票费用"

    try:
        response = tavily_client.search(
            query=query,
            search_depth="basic",
            include_answer=True
        )

        if response.get("answer"):
            return response["answer"]

        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}:{result['content']}")

        if not formatted_results:
            return "抱歉，没有找到相关的预算信息。"

        return "根据搜索，为您找到以下预算参考：\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误：查询预算信息时出现问题-{e}"


def show_map(city: str, attractions: str) -> str:
    """
    查询景点的地理位置信息（高德地图地理编码）

    Args:
        city: 城市名称
        attractions: 景点名称，多个用逗号分隔（如 "中山陵,夫子庙,玄武湖"）

    Returns:
        各景点的位置描述
    """
    api_key = GAODE_API_KEY
    if not api_key:
        return "错误：未配置 GAODE_API_KEY，无法使用地图功能。请在 .env 文件中添加 GAODE_API_KEY。"

    attraction_list = [a.strip() for a in attractions.split(",") if a.strip()]
    if not attraction_list:
        return "错误：未提供有效的景点名称。"

    results = []
    for name in attraction_list:
        try:
            resp = requests.get(
                "https://restapi.amap.com/v3/geocode/geo",
                params={"address": name, "city": city, "key": api_key},
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "1" and data.get("geocodes"):
                geo = data["geocodes"][0]
                formatted_address = geo.get("formatted_address", "未知")
                district = geo.get("district", "")
                location = geo.get("location", "")
                results.append(f"- {name}：位于{district}{formatted_address}（坐标：{location}）")
            else:
                results.append(f"- {name}：未找到位置信息")
        except Exception as e:
            results.append(f"- {name}：查询失败（{e}）")

    return f"📍 {city}景点位置信息：\n" + "\n".join(results)


def get_route(city: str, origin: str, destination: str, mode: str = "walk") -> str:
    """
    查询两个景点之间的路线（高德地图路径规划）

    Args:
        city: 城市名称
        origin: 出发地名称（如 "夫子庙"）
        destination: 目的地名称（如 "中山陵"）
        mode: 出行方式 walk(步行)/drive(驾车)/bus(公交)，默认步行

    Returns:
        路线描述（距离、时间、步骤）
    """
    api_key = GAODE_API_KEY
    if not api_key:
        return "错误：未配置 GAODE_API_KEY，无法使用路线功能。请在 .env 文件中添加 GAODE_API_KEY。"

    # 1. 先将地名转为坐标
    def geocode(place):
        resp = requests.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={"address": place, "city": city, "key": api_key},
            timeout=10,
        )
        data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            return data["geocodes"][0]["location"]
        return None

    origin_loc = geocode(origin)
    dest_loc = geocode(destination)
    if not origin_loc:
        return f"错误：无法定位出发地「{origin}」"
    if not dest_loc:
        return f"错误：无法定位目的地「{destination}」"

    # 2. 路径规划
    mode_map = {
        "walk": ("walking", "步行"),
        "drive": ("driving", "驾车"),
        "bus": ("transit/integrated", "公交"),
    }
    api_type, mode_name = mode_map.get(mode, ("walking", "步行"))

    try:
        url = f"https://restapi.amap.com/v3/direction/{api_type}"
        params = {
            "origin": origin_loc,
            "destination": dest_loc,
            "key": api_key,
        }
        if mode == "drive":
            params["strategy"] = 0  # 速度优先（时间最短）
        if mode == "bus":
            params["city1"] = city
            params["city2"] = city
            params["strategy"] = 0  # 推荐方案（时间最短优先）

        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get("status") != "1":
            return f"错误：路径规划失败 - {data.get('info', '未知错误')}"

        if mode == "walk":
            route = data.get("route", {})
            paths = route.get("paths", [])
            if not paths:
                return f"未找到从{origin}到{destination}的{mode_name}路线"
            # 按时间排序，取最短
            paths.sort(key=lambda p: int(p.get("duration", 0)))
            path = paths[0]
            distance = int(path.get("distance", 0))
            duration = int(path.get("duration", 0))
            steps = path.get("steps", [])
            steps_text = []
            for i, step in enumerate(steps[:8], 1):
                instruction = step.get("instruction", "")
                steps_text.append(f"  {i}. {instruction}")
            return (f"🚶 {origin} → {destination}（时间最短步行路线）\n"
                    f"距离：{distance}米，约{duration // 60}分钟\n"
                    f"路线：\n" + "\n".join(steps_text))

        elif mode == "drive":
            route = data.get("route", {})
            paths = route.get("paths", [])
            if not paths:
                return f"未找到从{origin}到{destination}的{mode_name}路线"
            # 按时间排序，取最短
            paths.sort(key=lambda p: int(p.get("duration", 0)))
            path = paths[0]
            distance = int(path.get("distance", 0))
            duration = int(path.get("duration", 0))
            steps = path.get("steps", [])
            steps_text = []
            for i, step in enumerate(steps[:8], 1):
                instruction = step.get("instruction", "")
                steps_text.append(f"  {i}. {instruction}")
            return (f"🚗 {origin} → {destination}（时间最短驾车路线）\n"
                    f"距离：{distance / 1000:.1f}公里，约{duration // 60}分钟\n"
                    f"路线：\n" + "\n".join(steps_text))

        elif mode == "bus":
            transits = data.get("route", {}).get("transits", [])
            if not transits:
                return f"未找到从{origin}到{destination}的公交路线"

            # 提取每条方案的线路信息和是否含地铁
            def extract_transit_info(transit):
                segments = transit.get("segments", [])
                lines = []
                has_subway = False
                for seg in segments:
                    # 地铁/城铁
                    railway = seg.get("railway", {})
                    if railway and railway.get("name"):
                        lines.append(railway["name"])
                        has_subway = True
                    # 公交
                    bus = seg.get("bus", {})
                    if bus and bus.get("buslines"):
                        line_name = bus["buslines"][0].get("name", "")
                        if line_name:
                            lines.append(line_name)
                return lines, has_subway

            # 优先选含地铁且时间最短的方案
            scored = []
            for t in transits:
                dur = int(t.get("duration", 0))
                lines, has_subway = extract_transit_info(t)
                # 含地铁的方案给 0.8 的时间权重，使其在时间相近时优先被选
                score = dur * (0.8 if has_subway else 1.0)
                scored.append((score, dur, lines, has_subway, t))

            scored.sort(key=lambda x: x[0])
            _, duration, lines, has_subway, transit = scored[0]

            lines_text = " → ".join(lines) if lines else "步行"
            tag = "地铁优先·时间最短" if has_subway else "时间最短公交路线"
            icon = "🚇" if has_subway else "🚌"
            return (f"{icon} {origin} → {destination}（{tag}）\n"
                    f"约{duration // 60}分钟，乘坐：{lines_text}")

    except Exception as e:
        return f"错误：路径规划请求失败-{e}"


# 将所有工具函数放入一个字典，方便后续调用
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
    "get_transport": get_transport,
    "get_restaurant": get_restaurant,
    "estimate_budget": estimate_budget,
    "show_map": show_map,
    "get_route": get_route,
}


# ============================================================================
# 🤖 LLM 客户端
# ============================================================================

class OpenAICompatibleClient:
    """
    一个用于调用任何兼容 OpenAI 接口的 LLM 服务的客户端。
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, messages: list[dict]) -> str:
        """调用 LLM API 来生成回应，接收完整的 messages 列表（含 system 消息）。"""
        print("正在调用大语言模型")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用 LLM API 时发生错误：{e}")
            return "错误：调用语言模型服务时出错。"


# ============================================================================
# 🔄 对话管理系统
# ============================================================================

# --- 1. 配置 LLM 客户端 ---
dotenv.load_dotenv(dotenv_path='../chapter02-model IO/.env')
API_KEY = os.getenv("OPENAI_API_KEY2")
BASE_URL = os.getenv("OPENAI_BASE_URL2")
MODEL_ID = "deepseek-v4-flash"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if TAVILY_API_KEY:
    os.environ['TAVILY_API_KEY'] = TAVILY_API_KEY
GAODE_API_KEY = os.getenv("GAODE_API_KEY")

llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)


class TravelAssistant:
    """旅行助手核心类，管理多轮对话状态（OpenAI messages 格式）"""

    def __init__(self):
        self.messages: list[dict] = []  # {"role": "user"|"assistant", "content": "..."}
        self.max_turns = 50  # 每个请求最多工具调用次数
        self.context_messages_limit = 10  # 保留最近的对话消息条数

    def reset(self):
        """清空对话历史"""
        self.messages = []
        print("✅ 对话历史已清空\n")

    def add_message(self, role: str, content: str):
        """添加消息到历史记录，使用 OpenAI messages 格式"""
        if role == "user":
            self.messages.append({"role": "user", "content": f"用户请求：{content}"})
        else:
            self.messages.append({"role": "assistant", "content": content})

        # 限制上下文大小，避免 token 浪费
        if len(self.messages) > self.context_messages_limit:
            self.messages = self.messages[-self.context_messages_limit:]

    def get_context_summary(self) -> str:
        """获取对话上下文摘要（用于系统提示）"""
        return f"当前支持的预设城市：{', '.join(SUPPORTED_CITIES)}"


# ============================================================================
# 🎮 交互模式
# ============================================================================

def _extract_action(llm_output: str) -> tuple[str, bool]:
    """
    从模型输出中提取 Thought 和 Action

    Returns:
        tuple: (action_text, found)
            - action_text: 提取到的 Thought-Action 文本，或原始输出
            - found: 是否成功匹配到 Thought-Action 格式
    """
    match = re.search(
        r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)',
        llm_output,
        re.DOTALL
    )
    if match:
        return match.group(1).strip(), True
    return llm_output.strip(), False


def _parse_action(action_str: str):
    """
    解析 Action 字符串

    Returns:
        dict: {"type": "finish"|"tool", "content": "..."}
    """
    # 从 Thought-Action 混合文本中提取 Action 部分
    action_match = re.search(r'Action:\s*(.*)', action_str, re.DOTALL)
    if action_match:
        action_str = action_match.group(1).strip()

    if action_str.startswith("Finish"):
        match = re.match(r"Finish\[(.*)]", action_str)
        if match:
            return {"type": "finish", "content": match.group(1)}
        return {"type": "finish", "content": action_str[len("Finish"):].strip("[]() ")}

    # 解析工具调用：function_name(arg_name="arg_value")
    tool_match = re.search(r'(\w+)\((.*)\)', action_str)
    if tool_match:
        tool_name = tool_match.group(1)
        args_str = tool_match.group(2)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))
        return {"type": "tool", "name": tool_name, "kwargs": kwargs}

    return {"type": "invalid", "content": action_str}


def _run_tool_cycle(assistant: TravelAssistant, verbose: bool = True):
    """
    运行单个工具调用循环（ReAct 模式）

    Args:
        assistant: TravelAssistant 实例，内部维护 messages 列表
        verbose: 是否打印详细信息

    Returns:
        str: 最终答案或观察结果
    """
    for i in range(assistant.max_turns):
        if verbose:
            print(f"\n--- 工具调用 #{i + 1} ---\n")

        # 构建带角色的 messages：system + 完整对话历史
        context_prompt = f"\n\n【系统提示】{assistant.get_context_summary()}"
        system_message = {"role": "system", "content": AGENT_SYSTEM_PROMPT + context_prompt}
        llm_messages = [system_message] + assistant.messages

        # 调用 LLM 进行思考
        llm_output = llm.generate(llm_messages)

        # 截断多余的 Thought-Action
        output_text, is_complete = _extract_action(llm_output)
        if output_text != llm_output.strip():
            if verbose:
                print("已截断多余的 Thought-Action 对")
            print(f"模型输出:\n{output_text}\n")
        else:
            if verbose:
                print(f"模型输出:\n{llm_output}\n")
            output_text = llm_output

        # 将 LLM 输出以 assistant 角色追加到对话历史
        assistant.messages.append({"role": "assistant", "content": output_text})

        # 解析 Action
        action_data = _parse_action(output_text)

        # 类型判断
        if action_data["type"] == "finish":
            if verbose:
                print(f"✅ 任务完成，最终答案:\n{action_data['content']}\n")
            return action_data['content']

        elif action_data["type"] == "tool":
            tool_name = action_data["name"]
            kwargs = action_data["kwargs"]

            if tool_name in available_tools:
                observation = available_tools[tool_name](**kwargs)
            else:
                observation = f"错误：未定义的工具 '{tool_name}'"

            # Observation 合并到当前 assistant 消息中，模型能看到完整的 Thought→Action→Observation
            observation_str = f"\nObservation: {observation}"
            if verbose:
                print(f"Observation: {observation}\n" + "=" * 40)
            assistant.messages[-1]["content"] += observation_str

        else:
            # 无效的 Action
            observation = "错误：未能解析到有效的 Action 字段。"
            observation_str = f"\nObservation: {observation}"
            if verbose:
                print(f"Observation: {observation}\n" + "=" * 40)
            assistant.messages[-1]["content"] += observation_str

    # 达到最大循环次数
    final_answer = "抱歉，我还没有找到满意的答案。请换个方式再试试。"
    if verbose:
        print(f"⚠️ 达到最大工具调用次数，最终答案：{final_answer}\n")
    assistant.messages.append({"role": "assistant", "content": f"结果：{final_answer}"})
    return final_answer


def run_interactive():
    """启动交互式多轮对话会话"""
    assistant = TravelAssistant()

    print("=" * 60)
    print("🌤️ 欢迎使用智能旅行助手！")
    print(f"💡 支持的预设城市：{', '.join(SUPPORTED_CITIES)}")
    print("📝 可用指令：exit (退出), clear (清空记录), help (帮助)")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！\n")
            break

        # 处理命令
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("👋 再见！\n")
            break
        elif user_input.lower() == 'clear':
            assistant.reset()
            continue
        elif user_input.lower() == 'help':
            print("""\n📖 使用指南:
   • 直接输入问题，例如："查询北京的天气"
   • 可以结合上文，例如："那上海呢？"（会继承上下文）
   • clear - 清空对话历史
   • exit - 退出程序
   """)
            continue

        if not user_input:
            continue

        # 开始处理单轮对话
        assistant.add_message("user", user_input)

        # _run_tool_cycle 内部直接操作 assistant.messages，保留完整的多轮对话上下文
        final_answer = _run_tool_cycle(assistant)
        assistant.add_message("result", f"结果：{final_answer}")

        print(f"\n{'=' * 60}\n")


def run_single_turn(user_prompt: str) -> list:
    """运行单次对话（保留原有脚本的简单用法）"""
    assistant = TravelAssistant()
    assistant.add_message("user", user_prompt)

    print(f"用户输入：{user_prompt}\n" + "=" * 40)

    final_answer = _run_tool_cycle(assistant, verbose=True)
    assistant.add_message("result", f"结果：{final_answer}")

    return assistant.messages


# ============================================================================
# 🚀 主程序入口
# ============================================================================

if __name__ == "__main__":
    # if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
    # 交互式模式
    # run_interactive()
    # else:
    # 默认单轮模式（保持兼容性）
    # user_prompt = "你好，请帮我查询一下今天南京的天气，然后根据天气推荐一个合适的旅游景点。"
    # run_single_turn(user_prompt)

    if len(sys.argv) > 1 and sys.argv[1] == "--single":

        # 单轮模式
        user_prompt = "你好，请帮我查询一下今天南京的天气，然后根据天气推荐一个合适的旅游景点。"
        run_single_turn(user_prompt)
    else:
        # 默认交互式多轮模式
        run_interactive()



