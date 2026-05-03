# pandoc_gui/polish_dialog.py
"""Preview dialog for heading polish results."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PolishPreviewDialog(QDialog):
    """Dialog showing heading fixes for user confirmation.

    Displays (original → fixed) pairs. User can confirm save or cancel.
    """

    def __init__(self, fixes: list[tuple[str, str]], hr_count: int = 0, parent=None):
        """Initialize dialog.

        Args:
            fixes: List of (original_heading, fixed_heading) tuples
            hr_count: Number of horizontal rules to be removed
        """
        super().__init__(parent)
        self.fixes = fixes
        self.hr_count = hr_count
        self.setWindowTitle("润色预览")
        self.setMinimumSize(500, 300)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        if not self.fixes and self.hr_count == 0:
            label = QLabel("所有标题无需修复")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        else:
            label = QLabel(f"发现 {len(self.fixes)} 处待修复")
            layout.addWidget(label)

            if self.hr_count > 0:
                hr_label = QLabel(f"将去除 {self.hr_count} 条分割线")
                hr_label.setStyleSheet("color: gray;")
                layout.addWidget(hr_label)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            container = QWidget()
            container_layout = QVBoxLayout(container)

            for original, fixed in self.fixes:
                item = QLabel(f"{original}  →  {fixed}")
                item.setWordWrap(True)
                container_layout.addWidget(item)

            container_layout.addStretch()
            scroll.setWidget(container)
            layout.addWidget(scroll, stretch=1)

        btn_layout = QVBoxLayout()
        self.confirm_btn = QPushButton("确认另存")
        self.confirm_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
