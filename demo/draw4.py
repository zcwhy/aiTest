import re
from graphviz import Digraph
import io
from PIL import Image
import matplotlib.pyplot as plt

def parse_mermaid_to_dot(mermaid_input):
    # 创建一个空的 Digraph 对象
    # dot = Digraph(comment='流程图', encoding='UTF-8',strict=True)
    dot = Digraph(comment='流程图', encoding='UTF-8')
    dot.attr('graph', fontname='SimSun', dpi='300')  # 设置字体和较高的 DPI
    dot.attr('node', fontname='SimSun', shape='rectangle', style='filled', fillcolor='#E1F5FE',
             fontcolor='black')  # 设置节点的样式
    dot.attr('edge', fontname='SimSun', color='#2196F3', fontcolor='black')  # 设置边的颜色

    # 提取节点和边的信息
    pattern = re.compile(r"([A-Z0-9]+)\[([^\]]+)\]")    # 提取所有匹配的节点和描述
    nodes_ = pattern.findall(mermaid_input)
    # 转换为指定格式
    nodes = [tuple(node) for node in nodes_]
    print(nodes)
    # edges = re.findall(r'(\w+)\s*-->\s*(\w+)', mermaid_input)
    # 正则表达式匹配字母之间的关系（包括可选的文字描述）
    # pattern = re.compile(r"([A-Z]+)(?:\[[^\]]*\])?\s*-->\s*([A-Z]+)(?:\[[^\]]*\])?")

    pattern_edges = re.compile(r"([A-Z0-9]+)(?:\[[^\]]*\])?\s*-->\s*([A-Z0-9]+)(?:\[[^\]]*\])?")

    # 提取所有匹配的关系
    edges = pattern_edges.findall(mermaid_input)

    # 提取所有匹配的关系
    # edges = pattern.findall(mermaid_input)
    print(edges)
    # 定义节点
    for node in nodes:
        dot.node(node[0], node[1])

    # 定义边
    for edge in edges:
        dot.edge(edge[0], edge[1])

    return dot


# 示例输入：Mermaid 格式图
mermaid_input = """
graph TD
    A[文件展示] --> B[搜索]
    A --> C[文件分类]
    A --> D[移动]
    A --> E[删除]
    A --> F[更多]
    B --> B1[按类型查找]
    B --> B2[按来源查找]
    B --> B3[按关键字查找]
    B --> B4[AI搜索]
    C --> C1[文档]
    C --> C2[图片]
    C --> C3[视频]
    C --> C4[音乐]
    C --> C5[压缩包]
    C --> C6[安装包]
    C --> C7[传输与下载]
    C --> C8[收藏]
    C --> C9[截屏]
    C --> C10[相机]
    C --> C11[录音机]
    D --> D1[选中文件]
    D --> D2[选择目录]
    E --> E1[删除文件]
    E --> E2[删除文件夹]
    E --> E3[删除系统文件]
    E --> E4[删除OTG文件]
    F --> F1[复制]
    F --> F2[设为私密]
    F --> F3[收藏]
    F --> F4[重命名]
    F --> F5[压缩]
    F --> F6[详情]
"""

# dot = parse_mermaid_to_dot(mermaid_input)

# print(dot.source)
#
# # 渲染图形为 PNG 文件
# dot.render('output_graph', format='png', cleanup=True)

# img = Image.open(img_stream)
#
# plt.imshow(img)
# plt.axis('off')
# plt.show()