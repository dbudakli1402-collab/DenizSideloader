"""Companion dialogs: progress, certificates, app IDs, pairing management."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class CompanionProgressDialog(QDialog):
    """3-step progress: download → install → pairing (iloader operation port)."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        lay.addWidget(t)
        self.rows: dict[str, QLabel] = {}
        for key, label in (("download", "Herunterladen"), ("install", "Installieren"), ("pairing", "Pairing")):
            row = QLabel(f"○ {label}")
            row.setObjectName("muted")
            lay.addWidget(row)
            self.rows[key] = row
        self.bar = QProgressBar()
        self.bar.setObjectName("bar")
        self.bar.setRange(0, 100)
        lay.addWidget(self.bar)
        self.hint = QLabel("Bitte iPhone nicht trennen.")
        self.hint.setObjectName("muted")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.hint)

    def update_step(self, step: str, frac: float, msg: str = "") -> None:
        order = ["download", "install", "pairing"]
        try:
            cur = order.index(step)
        except ValueError:
            cur = 0
        names = {"download": "Herunterladen", "install": "Installieren", "pairing": "Pairing"}
        for i, key in enumerate(order):
            lbl = self.rows[key]
            if i < cur:
                lbl.setText(f"✓ {names[key]}")
                lbl.setStyleSheet("color: #35d399;")
            elif i == cur:
                lbl.setText(f"● {names[key]} …")
                lbl.setStyleSheet("color: #1683ff; font-weight: 600;")
        self.bar.setValue(int(max(0.0, min(1.0, frac)) * 100))
        if msg:
            self.hint.setText(msg[:160])

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()  # don't cancel a running install by accident
            return
        super().keyPressEvent(event)


class CertificatesDialog(QDialog):
    revoke_requested = Signal(str)

    def __init__(self, profiles: list[Path], portal_locked: bool, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Zertifikate")
        self.setMinimumWidth(560)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("Entwicklungszertifikate")
        t.setObjectName("cardTitle")
        lay.addWidget(t)
        info = QLabel(
            "Lokale Provisioning-Profile (eigene Dateien). "
            + (
                "Apple-Portal-Zertifikate erscheinen hier, sobald die vollständige "
                "Apple-Anmeldung implementiert ist (Roadmap)."
                if portal_locked
                else ""
            )
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        lay.addWidget(info)
        self.list = QListWidget()
        for p in profiles:
            try:
                size = p.stat().st_size
            except Exception:
                size = 0
            QListWidgetItem(f"{p.name}  ·  {size // 1024} KB  ·  {p.parent}", self.list)
        if not profiles:
            QListWidgetItem("Keine lokalen Profile gefunden.", self.list)
        lay.addWidget(self.list)
        close = QPushButton("Schließen")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        lay.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


class AppIdsDialog(QDialog):
    def __init__(self, bundle_ids: list[str], portal_locked: bool, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("App-IDs")
        self.setMinimumWidth(520)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("App-IDs")
        t.setObjectName("cardTitle")
        lay.addWidget(t)
        info = QLabel(
            "Bundle-IDs aus deiner lokalen Bibliothek. "
            + (
                "Die Apple-Portal-Verwaltung (anlegen/löschen) folgt mit der vollständigen Apple-Anmeldung (Roadmap)."
                if portal_locked
                else ""
            )
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        lay.addWidget(info)
        lst = QListWidget()
        for bid in sorted(set(bundle_ids)):
            QListWidgetItem(bid, lst)
        if not bundle_ids:
            QListWidgetItem("Keine Einträge.", lst)
        lay.addWidget(lst)
        close = QPushButton("Schließen")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        lay.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


class PairingDialog(QDialog):
    export_requested = Signal()
    delete_requested = Signal()
    open_folder = Signal()

    def __init__(self, names: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pairing-Datei")
        self.setMinimumWidth(520)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(8)
        t = QLabel("Pairing-Dateien verwalten")
        t.setObjectName("cardTitle")
        lay.addWidget(t)
        info = QLabel("Lokale Einträge (nur Namen — Inhalte bleiben geheim):")
        info.setObjectName("muted")
        lay.addWidget(info)
        lst = QListWidget()
        for n in names:
            QListWidgetItem(n, lst)
        if not names:
            QListWidgetItem("Keine Einträge gefunden.", lst)
        lay.addWidget(lst)
        row = QHBoxLayout()
        b_exp = QPushButton("Exportieren …")
        b_exp.setObjectName("ghost")
        b_exp.clicked.connect(self.export_requested.emit)
        b_del = QPushButton("Gespeicherte löschen")
        b_del.setObjectName("danger")
        b_del.clicked.connect(self.delete_requested.emit)
        b_open = QPushButton("Ordner öffnen")
        b_open.setObjectName("ghost")
        b_open.clicked.connect(self.open_folder.emit)
        b_close = QPushButton("Schließen")
        b_close.setObjectName("primary")
        b_close.clicked.connect(self.accept)
        for b in (b_exp, b_del, b_open, b_close):
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)

    def pick_export_path(self, suggested: str) -> str:
        path, _ = QFileDialog.getSaveFileName(
            self, "Pairing-Datei exportieren", suggested, "Pairing (*.mobiledevicepairing);;Alle (*)"
        )
        return path

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
