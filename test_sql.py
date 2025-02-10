import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage

# 配置环境变量
os.environ["ZHIPUAI_API_KEY"] = "d9ae4d81e22cb9483f5b4d875ba2d1c1.0QNkBJCwDX7rLdI9"

class AnalysisState(TypedDict):
    messages: Annotated[list, add_messages]
    batch_counter: int

def initialize_chatbot():
    return ChatZhipuAI(
        model="glm-4-plus",
        temperature=0.2,
        streaming=True,
        max_retries=3
    )

# 修正后的批量处理函数
def batch_processor(file_path, batch_size=20):
    with open(file_path, 'r', encoding='utf-8') as f:
        batch = []
        for line in f:
            batch.append(line.strip())
            if len(batch) == batch_size:
                yield '\n'.join(batch)
                batch = []
        if batch:  # 处理剩余不足一个批次的数据
            yield '\n'.join(batch)

graph_builder = StateGraph(AnalysisState)
chat = initialize_chatbot()

def analysis_node(state: AnalysisState):
    response = chat.invoke(state["messages"])
    return {
        "messages": [response],
        "batch_counter": state["batch_counter"] + 1
    }

graph_builder.add_node("analyzer", analysis_node)
graph_builder.add_edge(START, "analyzer")
graph_builder.add_edge("analyzer", END)

app = graph_builder.compile()

def automated_analysis():
    answers = []
    processor = batch_processor('http_sql.txt', 20)  # 明确指定批次大小

    for idx, batch in enumerate(processor):
        # 统一格式化查询模板
        batch_header = f"第{idx+1}批次共{len(batch.split('\n'))}条记录："
        prompt = f"""你是一位经验丰富的网络安全专家，需要分析以下HTTP请求日志（{batch_header}）
================================
{batch}
================================
其中包含
- 时间戳ts
- 源ip id.orig_h
- 目标ip id.resp_h
- 请求uri
- 来源 referrer
- 用户agent信息 user-agent
你的任务是分析这些记录，判断是否存在sql注入攻击，并按照以下分类标准进行判断

1.高风险：sql注入攻击
- uri中包含sql关键字，如SELECT、UNION、INSERT、DROP、DELETE、UPDATE、EXEC、DATABASE()等
- uri中包含逻辑运算或恒等式，如OR '1'='1'、AND '1'='1'、--、#等
- 同时满足以上两个特点，该请求极可能是sql注入攻击，标记为高风险
2.可疑：可能是sql注入攻击
- 在referrer或者user-agent中包含sql关键字与逻辑运算或恒等式，这通常意味着一些非典型sql注入点
- 仅符合sql关键字或逻辑运算符之一，但不完全符合sql注入典型特征
- 需要进一步调查，标记为可疑
3.正常 无明显sql注入迹象
- 未发现sql关键字或异常逻辑运算符
- 看似正常的http请求，但仍需谨慎判断，标记为正常

分析要求
1.逐条分析：对每一条记录提供明确判断高风险、可疑或正常
2.提供理由：解释每条记录为何被判定为该类别，如发现的sql关键字，逻辑运算等
3.按照记录顺序输出：确保不遗漏任何条目
4.格式化输出：以清晰方式展示分析结果 
请找到其中的Sql注入攻击，并输出与攻击对应的时间戳、源IP、目标IP的信息，注意按照记录序号顺序进行，并且不要遗漏。请按照顺序分析每一条记录，并给出理由，无论是否可能包含Sql注入攻击
请按照以下顺序处理：
1. 逐条分析是否存在SQL注入特征
2. 判断风险等级（高/可疑/正常）
3. 说明判断依据（如出现SELECT、UNION等关键词）
4. 输出完整分析结果（包含时间戳、源IP、目标IP）"""

        response = app.invoke({
            "messages": [HumanMessage(content=prompt)],
            "batch_counter": idx
        }, {"configurable": {"thread_id": f"sql_test1_{idx}"}})  # 统一thread_id保持记忆

        answers.append(response["messages"][-1].content)
        print(f"成功处理第{idx+1}批次，记录数：{len(batch.split('\n'))}")
        answer_content = response["messages"][-1].content
        extraction_prompt = f"""请严格按以下要求处理分析结果：
        1. 筛选所有高风险和可疑记录
        2. 每条记录按格式输出：记录[序号]，风险等级[等级]，源IP[IP]，目标IP[IP]
        3. 严格保留原始序号
        4. 不要解释说明，直接输出结果
        5. 如果没有高风险与可疑记录，输出“无”即可，不要有多余输出

        示例正确格式：
        记录3，风险等级高风险，源IP192.168.1.10，目标IP10.0.0.2
        记录5，风险等级可疑，源IP172.16.0.5，目标IP10.0.0.2

        待处理的分析结果：
        {answer_content}"""

        # 创建独立对话（使用新的thread_id）
        extraction_response = chat.invoke([HumanMessage(content=extraction_prompt)])

        # 结构化写入汇总文件
        with open('answer_total.txt', 'a', encoding='utf-8') as total_f:
            # total_f.write(f"▼ 第{idx + 1}批次关键风险 ▼\n")
            total_f.write(extraction_response.content.strip())
            total_f.write("\n\n")

    with open('answer_sql.txt', 'w', encoding='utf-8') as f:
        f.write("\n\n—— 批次分隔 ——\n\n".join(answers))

    print(f"总共处理 {len(answers)} 个数据批次")

if __name__ == "__main__":
    automated_analysis()

