# Context

## 领域词汇

### 润色 (Polish)
对 Markdown 文件进行标题优化。核心场景：用户编写的 markdown 标题可能带有手动编号（如 `1.`, `1.1.`, `1.1.1.`），在与 pandoc 配合转 PDF 时会产生冲突。润色功能通过 LLM 检测并修复这些问题。

### 润色配置 (LLM Configuration)
用户提供的 LLM 访问凭证：
- **API URL** — LLM 端点，需兼容 OpenAI `/v1/chat/completions` 格式
- **API Key** — 访问密钥
- **Model** — 模型名称

### 标题提取 (Heading Extraction)
从 Markdown 文件中提取所有带 `#` 的标题行，准备发送给 LLM。

### 标题修复 (Heading Fix)
LLM 判断并返回需要修复的标题。返回格式为 `原标题|修复后标题`，每行一个。

### 批量润色 (Batch Polish)
文件夹模式下，对所有 `.md` 文件逐一进行润色处理。

### 润色预览 (Polish Preview)
展示润色建议，用户确认后再执行写入操作。

### 另存 (Save As)
润色后的内容不覆盖原文件，而是保存为新文件（如 `{原文件名}_polished.md`）。

## 关键约定

- **润色仅处理标题** — 不改变正文的润色行为
- **LLM 调用为批量处理** — 一个文件的所有标题一次性发送，而不是逐标题调用
- **先预览再保存** — 用户确认修改后再写入文件
- **文件夹模式下独立执行** — Run（PDF 转换）和润色是两个独立按钮，可按需点击

## 当前实现范围

- **GUI 框架**: PyQt6
- **LLM 接口**: OpenAI 兼容格式 (`/v1/chat/completions`)
- **转换引擎**: pandoc + xelatex
- **进程管理**: QProcess
