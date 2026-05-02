# Copyright (c) Opendatalab. All rights reserved.

import os
import subprocess
import sys
from pathlib import Path
import threading

try:
    from PyQt6.QtCore import QProcess, Qt, QThread, QEvent, pyqtSignal
    from PyQt6.QtWidgets import (
        QApplication,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QRadioButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    HAS_PYQT6 = True
except ImportError:
    HAS_PYQT6 = False


LATEX_TEMPLATE = r"""\documentclass[12pt,a4paper]{article}
\usepackage[includeheadfoot]{geometry}
\geometry{top=21mm,bottom=25.5mm,left=30mm,right=30mm}
\geometry{headheight=9mm,headsep=1mm,footskip=9mm}

\usepackage[T1]{fontenc}
\usepackage{xeCJK}
\usepackage{indentfirst}
\usepackage{setspace}
\usepackage{hyperref}

% Font setup - use Noto Sans CJK for Simplified Chinese
\setCJKmainfont{Noto Sans CJK SC}
\setmainfont{Times New Roman}

% Paragraph formatting
\setlength{\parindent}{2em}
\setlength{\parskip}{0pt}
\linespread{1.3}

% Heading styles - use bold weight
\usepackage{titlesec}
\titleformat{\section}{\bfseries\fontsize{14bp}{16.8bp}\selectfont}{\thesection}{1em}{}
\titleformat{\subsection}{\bfseries\fontsize{12bp}{14.4bp}\selectfont}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\bfseries\fontsize{12bp}{14.4bp}\selectfont}{\thesubsubsection}{1em}{}

% Pandoc-generated commands
\def\tightlist{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}

\begin{document}
$body$
\end{document}
"""


def build_command(input_path: str, output_dir: str) -> list[str]:
    """Build the pandoc command list for single file."""
    xelatex_path = str(Path.home() / "texlive" / "2026" / "bin" / "x86_64-linux" / "xelatex")

    # Write template to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
        f.write(LATEX_TEMPLATE)
        template_path = f.name

    cmd = [
        "uv", "run", "pandoc", input_path, "-o", output_dir,
        f"--pdf-engine={xelatex_path}",
        f"--template={template_path}",
    ]
    return cmd


def get_output_path(input_path: str, output_dir: str) -> str:
    """Compute output file path from input file and output directory."""
    input_p = Path(input_path)
    stem = input_p.stem
    output_file = Path(output_dir) / f"{stem}.pdf"
    return str(output_file)


def validate_input(path: str) -> str | None:
    """Validate input path. Returns error message or None if valid."""
    if not path or not path.strip():
        return "Input path is required."
    p = Path(path)
    if not p.exists():
        return f"Path does not exist: {path}"
    return None


_BaseWindow = QMainWindow if HAS_PYQT6 else object

MAX_LOG_LINES = 500

_qevent_type = None


def _get_polish_event_type():
    global _qevent_type
    if _qevent_type is None:
        _qevent_type = QEvent.Type(QEvent.registerEventType())
    return _qevent_type


class _PolishResultEvent(QEvent):
    """Custom event to carry polish result from thread to main thread."""

    def __init__(self, result):
        super().__init__(_get_polish_event_type())
        self.result = result  # (status, message_or_fixes, output_path)


class MinerUGui(_BaseWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pandoc GUI")
        self.setMinimumSize(600, 500)
        self.process = None
        self.file_queue = []
        self.output_dir = ""
        self.polish_thread = None
        self._batch_polish = False
        self._init_ui()
        self._load_llm_config()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Input path ---
        input_group = QGroupBox("Input Path")
        input_layout = QVBoxLayout(input_group)

        # Radio buttons for file/folder mode
        radio_layout = QHBoxLayout()
        self.radio_file = QRadioButton("File")
        self.radio_folder = QRadioButton("Folder")
        self.radio_file.setChecked(True)
        radio_layout.addWidget(self.radio_file)
        radio_layout.addWidget(self.radio_folder)
        radio_layout.addStretch()
        input_layout.addLayout(radio_layout)

        # Path input + browse button
        path_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Select input file or folder...")
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_input)
        path_layout.addWidget(self.input_path_edit)
        path_layout.addWidget(self.browse_btn)
        input_layout.addLayout(path_layout)

        layout.addWidget(input_group)

        # --- Output directory ---
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout(output_group)
        default_output = str(Path.home() / "Downloads" / "pandoc-output")
        self.output_dir_edit = QLineEdit(default_output)
        self.output_dir_edit.setPlaceholderText("Output directory...")
        self.output_browse_btn = QPushButton("Browse...")
        self.output_browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_browse_btn)
        layout.addWidget(output_group)

        # --- LLM Configuration ---
        llm_group = QGroupBox("LLM Configuration")
        llm_layout = QVBoxLayout(llm_group)
        self.llm_url_edit = QLineEdit()
        self.llm_url_edit.setPlaceholderText("API URL (e.g. https://api.openai.com/v1/chat/completions)")
        self.llm_key_edit = QLineEdit()
        self.llm_key_edit.setPlaceholderText("API Key")
        self.llm_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.llm_model_edit = QLineEdit()
        self.llm_model_edit.setPlaceholderText("Model (e.g. gpt-4)")
        llm_layout.addWidget(self.llm_url_edit)
        llm_layout.addWidget(self.llm_key_edit)
        llm_layout.addWidget(self.llm_model_edit)
        layout.addWidget(llm_group)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        self.polish_btn = QPushButton("润色")
        self.polish_btn.clicked.connect(self._polish)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.polish_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Log output ---
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group, stretch=1)

    def event(self, event):
        if event.type() == _get_polish_event_type():
            status = event.result[0]
            if status == "fixes":
                fixes, input_path, output_dir = event.result[1], event.result[2], event.result[3]
                self._handle_polish_fixes(fixes, input_path, output_dir)
            elif status == "error":
                err_msg = event.result[1]
                self.log_text.append(f"[FAILED] {err_msg}\n")
                if self._batch_polish:
                    self._polish_next()
                else:
                    self._on_polish_finished(False, err_msg)
            return True
        return super().event(event)

    def _handle_polish_fixes(self, fixes, input_path, output_dir):
        from pandoc_gui.polish_dialog import PolishPreviewDialog
        dialog = PolishPreviewDialog(fixes, self)
        if dialog.exec():
            # User confirmed - apply fixes and save
            try:
                from pandoc_gui.heading_fixer import apply_fixes
                with open(input_path, "r", encoding="utf-8") as f:
                    content = f.read()
                fixed_content = apply_fixes(content, fixes)
                p = Path(input_path)
                output_path = str(Path(output_dir) / f"{p.stem}_polished.md")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                self.log_text.append(f"[OK] {Path(output_path).name}\n")
                if self._batch_polish:
                    self._polish_next()
                else:
                    self.input_path_edit.setText(output_path)
                    self._on_polish_finished(True, f"润色完成: {output_path}")
            except Exception as e:
                self.log_text.append(f"[FAILED] {str(e)}\n")
                if self._batch_polish:
                    self._polish_next()
                else:
                    self._on_polish_finished(False, str(e))
        else:
            self.log_text.append("[已取消]\n")
            if self._batch_polish:
                self._polish_next()
            else:
                self._on_polish_finished(True, "已取消")

    def _load_llm_config(self):
        try:
            from pandoc_gui.config import load_llm_config
            config = load_llm_config()
            if config:
                self.llm_url_edit.setText(config.get("api_url", ""))
                self.llm_key_edit.setText(config.get("api_key", ""))
                self.llm_model_edit.setText(config.get("model", ""))
        except Exception:
            pass

    def _save_llm_config(self):
        try:
            from pandoc_gui.config import save_llm_config
            config = {
                "api_url": self.llm_url_edit.text().strip(),
                "api_key": self.llm_key_edit.text().strip(),
                "model": self.llm_model_edit.text().strip(),
            }
            save_llm_config(config)
        except Exception:
            pass

    def _get_llm_config(self):
        return {
            "api_url": self.llm_url_edit.text().strip(),
            "api_key": self.llm_key_edit.text().strip(),
            "model": self.llm_model_edit.text().strip(),
        }

    def _polish(self):
        input_path = self.input_path_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()
        is_folder = self.radio_folder.isChecked()

        # Validate LLM config
        llm_config = self._get_llm_config()
        if not llm_config["api_url"] or not llm_config["api_key"] or not llm_config["model"]:
            QMessageBox.warning(self, "LLM 配置不完整", "请填写完整的 API URL、Key 和 Model")
            return

        # Validate input
        error = validate_input(input_path)
        if error:
            QMessageBox.warning(self, "Invalid Input", error)
            return

        # Save LLM config
        self._save_llm_config()

        # Create output dir
        os.makedirs(output_dir, exist_ok=True)

        if is_folder:
            input_p = Path(input_path)
            md_files = list(input_p.glob("*.md"))
            if not md_files:
                QMessageBox.warning(self, "No Files", "No .md files found in the selected folder.")
                return
            self._polish_folder(list(md_files), output_dir, llm_config)
        else:
            self._batch_polish = False
            self._polish_single(input_path, output_dir, llm_config)

    def _polish_single(self, input_path: str, output_dir: str, llm_config: dict):
        self.log_text.clear()
        self.log_text.append(f"润色中: {input_path}\n")

        self.polish_btn.setEnabled(False)
        self.run_btn.setEnabled(False)

        def work():
            try:
                from pandoc_gui.polish_service import polish_file
                fixes = polish_file(input_path, output_dir, llm_config)
                result = "fixes", fixes, input_path, output_dir
            except Exception as e:
                result = "error", str(e), None, None

            from PyQt6.QtWidgets import QApplication
            QApplication.instance().postEvent(self, _PolishResultEvent(result))

        self.polish_thread = threading.Thread(target=work, daemon=True)
        self.polish_thread.start()

    def _polish_folder(self, md_files: list, output_dir: str, llm_config: dict):
        self.log_text.clear()
        self.log_text.append(f"找到 {len(md_files)} 个 Markdown 文件\n\n")
        self.file_queue = list(md_files)
        self.output_dir = output_dir
        self.llm_config = llm_config
        self._batch_polish = True
        self._polish_next()

    def _polish_next(self):
        if not self.file_queue:
            self.log_text.append("\n[润色完成]")
            self.polish_btn.setEnabled(True)
            self.run_btn.setEnabled(True)
            if self._batch_polish:
                self._notify("Pandoc GUI", "批量润色完成")
            return

        input_path = str(self.file_queue.pop(0))
        self.log_text.append(f"--- 润色中: {input_path} ---\n")
        self._polish_single(input_path, self.output_dir, self.llm_config)

    def _notify(self, title: str, message: str):
        QMessageBox.information(self, title, message)

    def _on_polish_finished(self, success: bool, message: str):
        self.polish_btn.setEnabled(True)
        self.run_btn.setEnabled(True)
        if success:
            self._notify("Pandoc GUI", message)
        else:
            QMessageBox.warning(self, "润色失败", message)

    def _browse_input(self):
        if self.radio_folder.isChecked():
            path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Input File", "",
                "Markdown Files (*.md);;All Files (*)"
            )
        if path:
            self.input_path_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self.output_dir_edit.setText(path)

    def _run(self):
        input_path = self.input_path_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()
        is_folder = self.radio_folder.isChecked()

        # Validate input
        error = validate_input(input_path)
        if error:
            QMessageBox.warning(self, "Invalid Input", error)
            return

        # Validate output
        if not output_dir:
            QMessageBox.warning(self, "Invalid Output", "Output directory is required.")
            return

        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)

        # Build command(s)
        if is_folder:
            input_p = Path(input_path)
            md_files = list(input_p.glob("*.md"))
            if not md_files:
                QMessageBox.warning(self, "No Files", "No .md files found in the selected folder.")
                return
            self._run_folder(md_files, output_dir)
        else:
            output_file = get_output_path(input_path, output_dir)
            self._run_single(input_path, output_file)

    def _run_single(self, input_path: str, output_file: str):
        """Run conversion for a single file."""
        cmd = build_command(input_path, output_file)

        self.log_text.clear()
        self.log_text.append(f"Converting: {input_path}\n")
        self.log_text.append(f"Output: {output_file}\n\n")

        def quote(s):
            return f"'{s}'" if ' ' in s else s
        display_cmd = ' '.join(quote(a) for a in cmd)
        self.log_text.append(f"$ {display_cmd}\n")

        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(Path(__file__).resolve().parent.parent))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_output)
        self.process.readyReadStandardError.connect(self._on_output)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)

        self.process.start(cmd[0], cmd[1:])

        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def _run_folder(self, md_files: list, output_dir: str):
        """Run conversion for multiple files sequentially."""
        self.log_text.clear()
        self.log_text.append(f"Found {len(md_files)} Markdown files\n\n")

        self.file_queue = list(md_files)
        self.output_dir = output_dir
        self._process_next_file()

    def _process_next_file(self):
        """Process the next file in the queue."""
        if not self.file_queue:
            self.log_text.append("\n[All files processed]")
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            self._notify("Pandoc GUI", "批量转换完成")
            return

        input_path = str(self.file_queue.pop(0))
        output_file = get_output_path(input_path, self.output_dir)

        self.log_text.append(f"--- Converting: {input_path} ---\n")

        cmd = build_command(input_path, output_file)

        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(Path(__file__).resolve().parent.parent))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_folder_output)
        self.process.readyReadStandardError.connect(self._on_folder_output)
        self.process.finished.connect(self._on_folder_finished)
        self.process.errorOccurred.connect(self._on_error)

        self.process.start(cmd[0], cmd[1:])

        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def _on_folder_output(self):
        """Handle output during folder processing."""
        if self.process:
            data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            if data:
                self.log_text.append(data.rstrip())
                doc = self.log_text.document()
                if doc.blockCount() > MAX_LOG_LINES:
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.movePosition(
                        cursor.MoveOperation.Down,
                        cursor.MoveMode.KeepAnchor,
                        doc.blockCount() - MAX_LOG_LINES,
                    )
                    cursor.removeSelectedText()
                sb = self.log_text.verticalScrollBar()
                sb.setValue(sb.maximum())

    def _on_folder_finished(self, exit_code, exit_status):
        """Handle folder file completion."""
        if exit_code == 0:
            self.log_text.append(f"[OK] {Path(self.file_queue[0] if self.file_queue else '').name if self.file_queue else ''}\n")
        else:
            self.log_text.append(f"[FAILED] exit code {exit_code}\n")

        self.process = None
        self._process_next_file()

    def _cancel(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.log_text.append("\n[Process cancelled by user]")
            self._notify("Pandoc GUI", "任务已取消")
        self.file_queue = []
        if self.polish_thread and self.polish_thread.is_alive():
            self.log_text.append("\n[润色任务取消]")
            self.polish_thread = None
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.polish_btn.setEnabled(True)

    def _on_output(self):
        if self.process:
            data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            if data:
                self.log_text.append(data.rstrip())
                # Trim excess lines to prevent lag
                doc = self.log_text.document()
                if doc.blockCount() > MAX_LOG_LINES:
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.movePosition(
                        cursor.MoveOperation.Down,
                        cursor.MoveMode.KeepAnchor,
                        doc.blockCount() - MAX_LOG_LINES,
                    )
                    cursor.removeSelectedText()
                # Auto-scroll to bottom
                sb = self.log_text.verticalScrollBar()
                sb.setValue(sb.maximum())

    def _on_finished(self, exit_code, exit_status):
        self.log_text.append(f"\n[Process finished with exit code {exit_code}]")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.process = None
        self.file_queue = []
        if exit_code == 0:
            self._notify("Pandoc GUI", "任务完成")
        else:
            self._notify("Pandoc GUI", f"任务失败 (退出码: {exit_code})")

    def _on_error(self, error):
        self.log_text.append(f"\n[Process error: {error.name}]")
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.process = None
        self.file_queue = []
        self._notify("Pandoc GUI", f"进程错误: {error.name}")

    def closeEvent(self, event):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "A pandoc process is still running. Terminate it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.process.kill()
                self.process.waitForFinished(3000)
                self.file_queue = []
                event.accept()
            else:
                event.ignore()
        elif self.file_queue:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                f"{len(self.file_queue)} files remaining in queue. Cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.file_queue = []
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print("Error: PyQt6 is not installed.")
        print("Install it with: uv pip install PyQt6")
        print("Or: pip install PyQt6")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MinerUGui()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
