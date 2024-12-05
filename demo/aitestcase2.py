import Agently
import json
from ENV import deep_seek_url, deep_seek_api_key, deep_seek_default_model
from md_to_txt import process_document
from draw4 import parse_mermaid_to_dot
import re
from graphviz import Digraph
import io
from PIL import Image

import matplotlib.pyplot as plt

# 将模型请求配置设置到agent工厂，确保后续由该工厂创建的所有agent对象都能继承这些配置
agent_factory = (
    Agently.AgentFactory()
    .set_settings("current_model", "OAIClient")
    .set_settings("model.OAIClient.url", deep_seek_url)
    .set_settings("model.OAIClient.auth", {"api_key": deep_seek_api_key})
    .set_settings("model.OAIClient.options", {"model": deep_seek_default_model})
)

# 定义一个类处理第一个阶段的输出
class StageOneResultHandler:
    def handle(self, mermaid_input):
        pass
        # print("绘制流程图......")
        # dot = parse_mermaid_to_dot(mermaid_input)
        # print(dot.source)
        # dot.render('output_graph', format='png', cleanup=True)
        return mermaid_input

# 创建一个工作流实例
workflow = Agently.Workflow()

# 主要工作：将需求文档中的业务模块归纳整理为摘要——————改成生成流程图
@workflow.chunk()
def first_question(inputs, storage):
    # 需求文档
    requirement_document = storage.get("requirement_document")

    # 创建需求分析agent来执行任务
    demand_agent = agent_factory.create_agent()

    # 设置需求分析agent的角色信息
    demand_agent.set_agent_prompt(
        "role",
        f"你是专业的需求分析工程师，擅长{requirement_document}的业务逻辑分析。"
    )

    flow_chart = (demand_agent.input(f"""针对{requirement_document}梳理业务流程，找出各个页面之间的流转关系，并使用mermaid代码输出。 \
                请根据{requirement_document}内容，不要提供任何文档之外的流程内容。 \
                {requirement_document}: """).start())

    # 保存流程图结果和需求agent
    storage.set("demand_agent", demand_agent)
    storage.set("flow_chart", flow_chart)

    # 返回阶段和结果
    return {
        "stage": "First Question：输出流程图的mermaid代码",
        "result": flow_chart
    }


@workflow.chunk()
def second_question(inputs, storage):

    requirement_document = storage.get("requirement_document")
    guiding_strategy = storage.get("guiding_strategy")
    case_template = storage.get("case_template")

    # 获取流程图内容
    flow_chart = storage.get("flow_chart")

    # 创建测试agent来执行任务
    test_agent = agent_factory.create_agent()

    # 设置测试agent的角色信息
    test_agent.set_agent_prompt(
        "role",
        f"你是专业的软件测试工程师，擅长对{requirement_document}进行测试用例编写。并且每次设计测试用例时都会按照{guiding_strategy}的指导方针进行"
    )

    # 发起流程图任务请求
    test_case = (test_agent.input(f"""对{requirement_document}的内容编辑测试用例,覆盖所有的{flow_chart}图的路径分支。并以{case_template}的测试用例进行测试用例编写，并使用markdown代码输出。 \
                  请根据{requirement_document}、{flow_chart}的内容，适当进行发散并优化（PRD里只是简要介绍，而测试点需要更多功能的交互）。 \
                  {requirement_document}: """).start())

    # 保存流程图结果和需求agent
    storage.set("test_agent", test_agent)
    storage.set("test_case", test_case)

    # 返回阶段和结果
    return {
        "stage": "Second Question：把PRD文档生成测试用例",
        "result": test_case,
        "flow_chart":flow_chart
    }


# 定义工作流运行关系
(
    workflow
    .connect_to("first_question")
    .connect_to("second_question")
    .connect_to("END")  # 连接到系统内置的end块
)

# 添加过程输出优化
@workflow.chunk_class()
def output_stage_result(inputs, storage):
    # 打印每个阶段的结果
    print(f"[{inputs['default']['stage']}]:\n", inputs["default"]["result"])
    return

# 连接输出节点到各工作块
(
    workflow.chunks["first_question"]
    .connect_to("@output_stage_result")
    .connect_to("second_question.wait")
)
(
    workflow.chunks["second_question"]
    .connect_to("@output_stage_result")
)

guiding_strategy_path = "../data/编写用例要点.txt"
with open(guiding_strategy_path, "r", encoding="utf-8") as file:
    guiding_strategy = file.read()

case_template_path = "../data/标准用例格式.txt"
with open(case_template_path, "r", encoding="utf-8") as file:
    case_template = file.read()


# 启动工作流并传入初始化存储数据
document_path = "../data/换机PRD.md"
result = workflow.start(storage={"requirement_document": process_document(document_path)[0],
                                 "guiding_strategy" : guiding_strategy,
                                 "case_template" : case_template})

requirement_summary = result.get("requirement_summary")

# 打印最终结果，使用json格式化输出
print("这个是")
print(json.dumps(result, indent=4, ensure_ascii=False))

test_cases = {}
test_case_content = result["default"]["result"]
flow_chart=result["default"]["flow_chart"]

pattern = r"测试用例编号: (\d+)\n([\s\S]*?)(?=\n####|$)"

matches = re.findall(pattern, test_case_content)

for match in matches:
    test_case_number = match[0]
    test_case_details = match[1].strip()
    test_cases[test_case_number] = test_case_details

# 打印格式化的结果
print(json.dumps(test_cases, indent=4, ensure_ascii=False))

print("结果:")
print(test_cases)

#test_cases是字典，key是用例编号，value是用例内容


print(flow_chart)

# dot = parse_mermaid_to_dot(flow_chart)
# dot.render('output_graph1', format='png', cleanup=True)
# img_stream = io.BytesIO(dot.pipe(format='png'))
# img = Image.open(img_stream)#流程图的变量

# print('--------优化---------')#暂时不用
# optimize_input = {"需求文档":text_pieces[0],"初步测试用例":test_case}
# from use_llm import Optimize
# print(Optimize(optimize_input))

