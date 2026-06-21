# AeroTutor 演示课件 PPT 生成说明书

> 把这份说明发给 Gemini，让它生成一段 Python 代码，运行后直接输出 `.pptx` 课件。

---

## 请为我生成一段 Python 代码，运行后创建一份航空航天 PPT 课件

### 代码要求

1. 使用 `python-pptx` 库（`from pptx import Presentation`）
2. 代码自包含：运行即生成 `航空航天基础讲义.pptx`，无需额外输入
3. 幻灯片尺寸为标准 16:9
4. 每页标题用 `Title 1` 样式，正文用 18pt 字号

### PPT 结构（共 7 页）

| 页码 | 标题 | 内容 |
|------|------|------|
| 1 | 航空航天工程基础 | 副标题：大二课程讲义 · 4 大核心知识点 |
| 2 | 伯努利原理 | 概念 + 伯努利方程 p+½ρv²+ρgh=const + 常见误区（有人误以为流速越快压强越大） |
| 3 | 机翼升力 | 上下翼面流速差异 + 升力公式 L=½ρv²SCL + 飞机实例 |
| 4 | 雷诺数 | 层流 vs 湍流 + 公式 Re=ρvL/μ + 飞行器设计中的应用 |
| 5 | 激波 | 超音速流动 + 马赫数 Ma>1 + 音障现象 |
| 6 | 核心公式汇总 | 伯努利方程 / 升力公式 / 雷诺数 / 马赫数 4 个公式 |
| 7 | 复习思考题 | 3 道思考题（不附答案）：①机翼升力与攻角的关系？②高雷诺数对飞行阻力的影响？③激波产生后气流参数如何变化？ |

### 每页内容要求

- 第 2-5 页：每页至少 100 字正文 + 1 个公式 + 1 个航空实例
- 使用项目符号列表（bullet points）组织正文
- 公式用纯文本格式写在单独一行，加粗
- 在第 2 页刻意插入一句常见误区：「有人认为流速越快压强越大」

### 代码模板参考

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_slide(prs, title, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = title
    body = slide.shapes.placeholders[1].text_frame
    for b in bullets:
        p = body.add_paragraph()
        p.text = b
        p.level = 0
        for run in p.runs:
            run.font.size = Pt(18)

add_slide(prs, "伯努利原理", [
    "概念：理想流体在定常流动中，沿流线的能量守恒关系",
    "伯努利方程：p + ½ρv² + ρgh = 常数",
    ...
])

prs.save("航空航天基础讲义.pptx")
print("PPT 已生成")
```

请按以上结构生成完整 Python 代码，直接输出可运行脚本。

---

## 使用说明

1. 把上述内容发给 Gemini（gemini.google.com）
2. 复制 Gemini 生成的 Python 代码，保存为 `generate_ppt.py`
3. 终端运行 `python generate_ppt.py`
4. 生成的 `航空航天基础讲义.pptx` 上传到 AeroTutor
5. 演示时可以提问：
   - 「用伯努利原理解释机翼为什么能飞」
   - 「帮我出 3 道测验题」
   - 「生成 5 张知识闪卡」
   - 「分析我的学习薄弱点」
   - 「帮我总结知识库核心重点」
