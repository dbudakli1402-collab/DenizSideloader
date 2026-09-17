"""First-launch setup wizard: 5 steps, no console."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWizard, QWizardPage

STEPS = [
    ("Welcome to Deniz Sideloader", "Connect your iPhone to get started."),
    ("1. Connect iPhone", "Plug in your iPhone via USB and unlock it."),
    ("2. Trust this computer", "On the iPhone, tap \u201cTrust\u201d when prompted."),
    (
        "3. Check Apple requirements",
        "Free Apple IDs sign apps for 7 days; paid memberships last longer. See Settings \u2192 Signing.",
    ),
    ("4. Choose an IPA", "Import an .ipa into the library or paste a direct download URL."),
    (
        "5. Install",
        "Select IPA \u2192 select iPhone \u2192 Install. Do not disconnect during install.",
    ),
]


class FirstLaunchWizard(QWizard):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to Deniz Sideloader")
        self.setMinimumSize(520, 380)
        for title, body in STEPS:
            page = QWizardPage()
            page.setTitle(title)
            layout = QVBoxLayout(page)
            label = QLabel(body)
            label.setWordWrap(True)
            layout.addWidget(label)
            if title.startswith("Welcome"):
                btn = QPushButton("Connect iPhone")
                btn.setObjectName("primary")
                btn.clicked.connect(self.next)
                layout.addWidget(btn)
            self.addPage(page)
        self.setButtonText(QWizard.WizardButton.FinishButton, "Get started")
