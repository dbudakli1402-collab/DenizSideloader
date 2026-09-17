"""Animated toast notifications (success / error / info), auto-dismissing."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui import design as D
from app.ui.icons import icon as make_icon


class _Toast(QFrame):
    def __init__(self, kind: str, title: str, body: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setFixedWidth(360)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(12)
        glyph = {"success": "check", "error": "warn", "info": "bell"}.get(kind, "bell")
        color = {"success": D.GREEN, "error": D.RED, "info": D.CYAN}.get(kind, D.CYAN)
        pic = QLabel()
        pic.setPixmap(make_icon(glyph, 22, color).pixmap(26, 26))
        lay.addWidget(pic, alignment=Qt.AlignmentFlag.AlignTop)
        box = QVBoxLayout()
        box.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("toastTitle")
        t.setWordWrap(True)
        b = QLabel(body)
        b.setObjectName("toastBody")
        b.setWordWrap(True)
        box.addWidget(t)
        box.addWidget(b)
        lay.addLayout(box, 1)
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._anim = QPropertyAnimation(self._opacity, b"opacity", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def fade_in(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def fade_out(self, done) -> None:
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        try:
            self._anim.finished.disconnect()
        except Exception:
            pass
        self._anim.finished.connect(done)
        self._anim.start()


class ToastManager(QWidget):
    """Overlay in the bottom-right corner of the main window."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._box = QVBoxLayout(self)
        self._box.setContentsMargins(0, 0, 18, 18)
        self._box.setSpacing(10)
        self._box.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self._toasts: list[_Toast] = []
        self.raise_()

    def show_toast(self, kind: str, title: str, body: str = "", ms: int = 4200) -> None:
        toast = _Toast(kind, title, body, self)
        self._box.addWidget(toast, alignment=Qt.AlignmentFlag.AlignRight)
        self._toasts.append(toast)
        while len(self._toasts) > 4:
            old = self._toasts.pop(0)
            old.deleteLater()
        toast.fade_in()
        QTimer.singleShot(ms, lambda: self._dismiss(toast))

    def _dismiss(self, toast: _Toast) -> None:
        if toast not in self._toasts:
            return

        def _gone() -> None:
            if toast in self._toasts:
                self._toasts.remove(toast)
            toast.deleteLater()

        toast.fade_out(_gone)

    def resize_to_parent(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())

    # convenience
    def success(self, title: str, body: str = "") -> None:
        self.show_toast("success", title, body)

    def error(self, title: str, body: str = "") -> None:
        self.show_toast("error", title, body, ms=6000)

    def info(self, title: str, body: str = "") -> None:
        self.show_toast("info", title, body)
