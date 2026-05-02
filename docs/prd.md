# pandoc-gui PRD

## Problem Statement

用户需要将 Markdown 文件批量转换为 PDF，目前需要手动在终端执行 pandoc 命令，操作不够直观，缺乏图形界面。

## Solution

构建一个 PyQt6 图形界面工具，封装 pandoc 命令，提供 File/Folder 模式切换、路径选择、转换执行和日志输出功能。

## User Stories

1. 作为用户，我希望通过图形界面选择单个 Markdown 文件并转换为 PDF，无需记忆 pandoc 命令行参数
2. 作为用户，我希望通过图形界面选择包含多个 Markdown 文件的文件夹，批量转换为 PDF
3. 作为用户，我希望在转换过程中看到实时日志输出，了解转换进度和错误信息
4. 作为用户，我希望能够取消正在进行的转换任务
5. 作为用户，我希望通过系统菜单快捷方式启动程序，无需打开终端
6. 作为用户，我希望程序在任务完成或出错时收到系统通知提醒
7. 作为用户，我希望转换完成后输出文件保存在我指定的目录中
8. 作为用户，我需要在关闭程序时得到确认提示，如果转换任务仍在运行

## Implementation Decisions

- **GUI 框架**: PyQt6
- **环境管理**: uv 虚拟环境
- **PDF 引擎**: xelatex（已安装在系统中）
- **项目结构**:
  - `~/codes/pandoc-gui/pyproject.toml` - 项目配置和依赖声明
  - `~/codes/pandoc-gui/pandoc_gui/__init__.py` - 包初始化
  - `~/codes/pandoc-gui/pandoc_gui/gui.py` - 主 GUI 逻辑
  - `~/.local/share/applications/pandoc-gui.desktop` - 桌面快捷方式
- **入口点**: `uv run python -m pandoc_gui.gui`
- **命令封装**: `uv run pandoc` 执行转换命令
- **进程管理**: 使用 QProcess 管理子进程，支持取消操作

### 模块设计

#### pandoc_gui.gui.MinerUGui (主窗口类)
- `__init__()`: 初始化主窗口，设置最小尺寸
- `_init_ui()`: 构建界面组件（GroupBox, RadioButton, LineEdit, Button, TextEdit）
- `_browse_input()`: 打开文件/文件夹选择对话框
- `_browse_output()`: 打开目录选择对话框
- `_run()`: 校验输入，执行转换命令
- `_cancel()`: 终止正在运行的进程
- `_on_output()`: 读取并显示进程输出
- `_on_finished()`: 处理进程结束事件
- `_on_error()`: 处理进程错误事件
- `closeEvent()`: 窗口关闭事件处理

#### pandoc_gui.gui.build_command(input_path, output_dir, backend)
- 构建 pandoc CLI 命令列表
- 返回: `["uv", "run", "pandoc", input_path, "-o", output_dir, "--pdf-engine=xelatex"]`

#### pandoc_gui.gui.validate_input(path)
- 验证输入路径有效性
- 返回: `None`（有效）或错误消息字符串（无效）

## Testing Decisions

- 单元测试 `build_command` 函数：验证不同输入模式下命令构建正确性
- 单元测试 `validate_input` 函数：验证路径校验逻辑
- 测试覆盖场景：
  - 有效的文件路径
  - 有效的文件夹路径
  - 空路径
  - 不存在的路径
  - GPU 模式命令构建
  - CPU 模式命令构建

## Out of Scope

- PDF 模板选择（后续扩展）
- 目录生成（toc）开关（后续扩展）
- 代码高亮选项（后续扩展）
- 转换进度百分比显示
- 预览功能
- 多语言界面

## Further Notes

- 参考实现: `~/codes/MinerU/mineru/cli/gui.py`
- 依赖 PyQt6 需要在 `pyproject.toml` 中声明
- `.desktop` 文件需要软链接到 `~/.local/share/applications/`
