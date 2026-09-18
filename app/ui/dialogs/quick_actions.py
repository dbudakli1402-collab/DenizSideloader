"""Quick-action dialogs: sign, bundle ID, profiles, URL download, QR."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.ipa.models import IpaInfo
from app.signing.local_provisioning import list_profiles
from app.ui import design as D


class UrlDownloadDialog(QDialog):
    start = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Von URL laden")
        self.setMinimumWidth(480)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        t = QLabel("Direkte IPA-URL eingeben (nur https).")
        t.setObjectName("muted")
        lay.addWidget(t)
        self.input = QLineEdit()
        self.input.setPlaceholderText("https://beispiel.de/app.ipa")
        lay.addWidget(self.input)
        row = QHBoxLayout()
        ok = QPushButton("Herunterladen")
        ok.setObjectName("primary")
        ok.clicked.connect(self._go)
        no = QPushButton("Abbrechen")
        no.setObjectName("ghost")
        no.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(no)
        row.addStretch(1)
        lay.addLayout(row)

    def _go(self) -> None:
        self.start.emit(self.input.text())
        self.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


class QrDialog(QDialog):
    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("QR-Code")
        self.setMinimumWidth(380)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        info = QLabel("QR-Code für einen Download-Link erzeugen und z. B. an ein Zweitgerät weitergeben.")
        info.setObjectName("muted")
        info.setWordWrap(True)
        lay.addWidget(info)
        self.input = QLineEdit()
        self.input.setPlaceholderText("https://beispiel.de/app.ipa")
        self.input.setText(text)
        self.input.textChanged.connect(lambda: self._render())
        lay.addWidget(self.input)
        self.pic = QLabel()
        self.pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pic.setMinimumSize(240, 240)
        lay.addWidget(self.pic)
        self._render()

    def _render(self) -> None:
        from PySide6.QtGui import QImage, QPixmap

        text = self.input.text().strip()
        if not text:
            self.pic.clear()
            return
        try:
            import qrcode

            qr = qrcode.make(text, box_size=6, border=2)
            img = qr.convert("RGB")
            data = img.tobytes()
            qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            self.pic.setPixmap(QPixmap.fromImage(qimg).scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as exc:
            self.pic.setText(f"QR-Fehler: {exc}"[:200])

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


class SignDialog(QDialog):
    sign_now = Signal(object, object)  # (provider, identity)

    def __init__(self, ipa: IpaInfo | None, identities: list, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("IPA signieren")
        self.setMinimumWidth(480)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.addWidget(QLabel(f"Datei: {ipa.display_title if ipa else '–'}"))
        lay.addWidget(_muted("Mit deinem eigenen Zertifikat signieren. Das Passwort wird nie gespeichert."))
        self.combo = QComboBox()
        self._idents = identities
        for _prov, ident in identities:
            self.combo.addItem(f"{ident.label}  ({ident.expiry_text})")
        lay.addWidget(self.combo)
        if not identities:
            warn = QLabel(
                "Keine Signierungs-Identität verfügbar. Lege zuerst ein Provisioning-Profil unter Einstellungen ab."
            )
            warn.setWordWrap(True)
            warn.setStyleSheet(f"color: {D.AMBER};")
            lay.addWidget(warn)
        row = QHBoxLayout()
        ok = QPushButton("Signieren")
        ok.setObjectName("primary")
        ok.setEnabled(bool(identities and ipa))
        ok.clicked.connect(self._go)
        no = QPushButton("Abbrechen")
        no.setObjectName("ghost")
        no.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(no)
        row.addStretch(1)
        lay.addLayout(row)

    def _go(self) -> None:
        idx = self.combo.currentIndex()
        if 0 <= idx < len(self._idents):
            self.sign_now.emit(*self._idents[idx])
        self.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


class BundleIdDialog(QDialog):
    apply_now = Signal(str)

    def __init__(self, current: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bundle-ID ändern")
        self.setMinimumWidth(460)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.addWidget(QLabel(f"Aktuell: {current}"))
        lay.addWidget(_muted("Nur für eigene Apps — die neue ID muss zu deinem Provisioning-Profil passen."))
        self.input = QLineEdit()
        self.input.setPlaceholderText("com.deinname.appname")
        self.input.setText(current)
        lay.addWidget(self.input)
        self.err = QLabel("")
        self.err.setStyleSheet(f"color: {D.RED};")
        lay.addWidget(self.err)
        row = QHBoxLayout()
        ok = QPushButton("Übernehmen")
        ok.setObjectName("primary")
        ok.clicked.connect(self._go)
        no = QPushButton("Abbrechen")
        no.setObjectName("ghost")
        no.clicked.connect(self.reject)
        row.addWidget(ok)
        row.addWidget(no)
        row.addStretch(1)
        lay.addLayout(row)

    def _go(self) -> None:
        from app.ipa.repackage import validate_bundle_id

        try:
            validate_bundle_id(self.input.text())
        except ValueError as exc:
            self.err.setText(str(exc))
            return
        self.apply_now.emit(self.input.text().strip())
        self.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


class ProfilesDialog(QDialog):
    use_folder = Signal(str)

    def __init__(self, search_dirs: list[Path], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Provisioning-Profile")
        self.setMinimumWidth(520)
        self.setModal(True)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.addWidget(_muted("Gefundene .mobileprovision-Dateien (nur Namen, keine Inhalte):"))
        self.list = QLabel("–")
        self.list.setObjectName("muted")
        self.list.setWordWrap(True)
        lay.addWidget(self.list)
        found = list_profiles(search_dirs)
        if found:
            self.list.setText("\n".join(f"• {p.name}  ({p.parent})" for p in found[:20]))
        else:
            self.list.setText("Keine Profile in den Suchordnern gefunden.")
        row = QHBoxLayout()
        pick = QPushButton("Ordner wählen")
        pick.setObjectName("ghost")
        pick.clicked.connect(self._pick)
        close = QPushButton("Schließen")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        row.addWidget(pick)
        row.addWidget(close)
        row.addStretch(1)
        lay.addLayout(row)

    def _pick(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Provisioning-Ordner")
        if d:
            self.use_folder.emit(d)
            self.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)


def _muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("muted")
    label.setWordWrap(True)
    return label
