# Volterra Wiki：构建验证加固与公式围栏修复（2026-11-17）

## 发现与根因

检查提交 `df29c8d` 对应的 Actions 运行时，Build 在阅读器公式数量检查处失败：章节正则扫描得到 1563 项，MathJax 阅读器实际识别 1544 项。差额 19 项恰好来自四处数学围栏内部混入的行内公式与中文解释。问题位于第 04 章一处、第 05 章两处、第 06 章一处。

## 修复

- 把四处围栏内部的解释性段落移回 Markdown 正文；第 05 章 POD 分解段落按“公式—解释—公式”重新划分两个数学围栏。
- 同步更新 downloads/ 里的七章合订版，保留原有数学含义与图像引用。
- 新增 `tools/figure_manifest.txt`，固定现行 37 张图的文件名清单。
- 新增 `tools/validate_sources.py`，在 npm 构建前检查 math 围栏中的误入正文、SVG XML 与 1600×980 画布、每章配图数量和 Markdown 本地文件链接。
- 在既有 reader.yml Build job 中加入严格静态检查，保留 Node.js 24、原触发条件和 Pages 部署方式。主分支构建另运行网络依赖的 GitHub 原生公式预览检查；外部页面请求失败时发出 CI 警示，不阻塞已通过本地 MathJax 的发布流程。

## 验收与边界

严格检查仍以 `npm run --prefix tools/reader build` 的同步章节和 MathJax 渲染为准。新的 XML 检查验证 SVG 源码结构与画布元数据；文字重叠、遮挡、字号及实际图形显示继续需要浏览器视觉抽查。部署结果以该次 GitHub Actions 的 Build 与 publish job 实际状态为准。
