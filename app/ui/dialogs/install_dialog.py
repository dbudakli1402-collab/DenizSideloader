"""Installation progress dialog following the honest workflow steps."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout

from app.installation.models import ORDERED_STEPS, STEP_LABELS, InstallationJob, InstallStep


class InstallDialog(QDialog):
    def __init__(self, job: InstallationJob, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Installing {job.app_name or 'app'}")
        self.setMinimumWidth(460)
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        self.title = QLabel(f"Installing {job.app_name or job.ipa_path}")
        self.title.setObjectName("cardTitle")
        layout.addWidget(self.title)
        self.step_labels: dict[InstallStep, QLabel] = {}
        for step in ORDERED_STEPS:
            if step == InstallStep.DONE:
                continue
            lbl = QLabel(f"\u25cb {STEP_LABELS[step]}")
            lbl.setObjectName("muted")
            layout.addWidget(lbl)
            self.step_labels[step] = lbl
        self.bar = QProgressBar()
        self.bar.setObjectName("bar")
        self.bar.setRange(0, 100)
        layout.addWidget(self.bar)
        self.hint = QLabel("Do not disconnect your iPhone.")
        self.hint.setObjectName("muted")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hint)

    def update_job(self, job: InstallationJob) -> None:
        from pathlib import Path

        self.title.setText(f"Installing {job.app_name or Path(job.ipa_path).name}")
        self.bar.setValue(int(job.progress * 100))
        order = [s for s in ORDERED_STEPS if s != InstallStep.DONE]
        try:
            cur_idx = order.index(job.step) if job.step in order else len(order)
        except ValueError:
            cur_idx = len(order)
        for i, step in enumerate(order):
            lbl = self.step_labels.get(step)
            if not lbl:
                continue
            if i < cur_idx:
                lbl.setText(f"\u2713 {STEP_LABELS[step]}")
                lbl.setStyleSheet("color: #30d158;")
            elif i == cur_idx and job.step != InstallStep.FAILED:
                lbl.setText(f"\u25cf {STEP_LABELS[step]}\u2026")
                lbl.setStyleSheet("color: #0a84ff; font-weight: 600;")
            else:
                lbl.setText(f"\u25cb {STEP_LABELS[step]}")
                lbl.setStyleSheet("color: #8b919c;")
        if job.step == InstallStep.FAILED:
            self.hint.setText(f"{job.error_title}: {job.error_detail[:300]}")
            self.hint.setStyleSheet("color: #ff9d9d;")
        elif job.step == InstallStep.DONE:
            self.hint.setText(f"{job.app_name} was successfully installed on your iPhone.")
            self.hint.setStyleSheet("color: #30d158;")
