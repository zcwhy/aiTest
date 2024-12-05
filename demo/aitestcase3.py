import Agently
import json
from ENV import deep_seek_url, deep_seek_api_key, deep_seek_default_model
from md_to_txt import process_document
from draw4 import parse_mermaid_to_dot
import re
from graphviz import Digraph
import io
from PIL import Image
from tools import get_case_list


class WorkflowManager:
    def __init__(self):
        # 将模型请求配置设置到agent工厂，确保后续由该工厂创建的所有agent对象都能继承这些配置
        self.agent_factory = (
            Agently.AgentFactory()
           .set_settings("current_model", "OAIClient")
           .set_settings("model.OAIClient.url", deep_seek_url)
           .set_settings("model.OAIClient.auth", {"api_key": deep_seek_api_key})
           .set_settings("model.OAIClient.options", {"model": deep_seek_default_model})
        )
        self.workflow = Agently.Workflow()
        self.guiding_strategy = None
        self.case_template = None
        self.requirement_document = None
        self.initialize_workflow()

    def initialize_workflow(self):
        # 主要工作：将需求文档中的业务模块归纳整理为摘要——————改成生成流程图
        @self.workflow.chunk()
        def first_question(inputs, storage):
            # 创建需求分析agent来执行任务
            demand_agent = self.agent_factory.create_agent()
            # 设置需求分析agent的角色信息
            demand_agent.set_agent_prompt(
                "role",
                f"你是专业的需求分析工程师，擅长{self.requirement_document}的业务逻辑分析。"
            )

            flow_chart = (demand_agent.input(f"""针对{self.requirement_document}梳理业务流程，找出各个页面之间的流转关系，并使用mermaid代码输出。 \
                            请根据{self.requirement_document}内容，不要提供任何文档之外的流程内容。 \
                            {self.requirement_document}: """).start())

            # 保存流程图结果和需求agent
            storage.set("demand_agent", demand_agent)
            storage.set("flow_chart", flow_chart)

            # 返回阶段和结果
            return {
                "stage": "First Question：输出流程图的mermaid代码",
                "result": flow_chart
            }

        @self.workflow.chunk()
        def second_question(inputs, storage):
            flow_chart = storage.get("flow_chart")

            # 创建测试agent来执行任务
            test_agent = self.agent_factory.create_agent()
            # 设置测试agent的角色信息
            test_agent.set_agent_prompt(
                "role",
                f"你是专业的软件测试工程师，擅长对{self.requirement_document}进行测试用例编写。并且每次设计测试用例时都会按照{self.guiding_strategy}的指导方针进行"
            )

            # 发起流程图任务请求
            test_case = (test_agent.input(f"""对{self.requirement_document}的内容编辑测试用例,覆盖所有的{flow_chart}图的路径分支。并以{self.case_template}的测试用例进行测试用例编写，并使用markdown代码输出。 \
                              请根据{self.requirement_document}、{flow_chart}的内容，适当进行发散并优化（PRD里只是简要介绍，而测试点需要更多功能的交互）。 \
                              {self.requirement_document}: """).start())

            # 保存流程图结果和需求agent
            storage.set("test_agent", test_agent)
            storage.set("test_case", test_case)
            print("是不是这里")
            print(test_case)
            # 返回阶段和结果
            return {
                "stage": "Second Question：把PRD文档生成测试用例",
                "result": test_case,
                "flow_chart": flow_chart
            }

        # 定义工作流运行关系
        (
            self.workflow
           .connect_to("first_question")
           .connect_to("second_question")
           .connect_to("END")  # 连接到系统内置的end块
        )

        # 添加过程输出优化
        @self.workflow.chunk_class()
        def output_stage_result(inputs, storage):
            # 打印每个阶段的结果
            print(f"[{inputs['default']['stage']}]:\n", inputs["default"]["result"])
            return

        # 连接输出节点到各工作块
        (
            self.workflow.chunks["first_question"]
           .connect_to("@output_stage_result")
           .connect_to("second_question.wait")
        )
        (
            self.workflow.chunks["second_question"]
           .connect_to("@output_stage_result")
        )

    def load_strategy_and_template(self, guiding_strategy_path, case_template_path):
        with open(guiding_strategy_path, "r", encoding="utf-8") as file:
            self.guiding_strategy = file.read()
        with open(case_template_path, "r", encoding="utf-8") as file:
            self.case_template = file.read()

    def set_requirement_document(self, document_path):
        self.requirement_document = process_document(document_path)[0]

    def run_workflow(self):
        result = self.workflow.start(storage={
            "requirement_document": self.requirement_document,
            "guiding_strategy": self.guiding_strategy,
            "case_template": self.case_template
        })

        test_case_content = result["default"]["result"]
        test_cases = {}
        test_cases = get_case_list(test_case_content)
        print("结果1：")
        print(test_cases)
        return test_cases


if __name__ == "__main__":
    manager = WorkflowManager()
    guiding_strategy_path = "../data/编写用例要点.txt"
    case_template_path = "../data/标准用例格式.txt"
    manager.load_strategy_and_template(guiding_strategy_path, case_template_path)
    document_path = "../data/相册PRD.md"
    manager.set_requirement_document(document_path)
    test_cases = manager.run_workflow()
    print(json.dumps(test_cases, indent=4, ensure_ascii=False))
    print("结果2:")
    print(test_cases)
    # test_cases是字典，key是用例编号，value是用例内容