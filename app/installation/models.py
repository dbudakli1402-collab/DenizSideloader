"""Installation job models + state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class InstallStep(str, Enum):
    SELECT = "select"
    ANALYZE = "analyze"
    DETECT = "detect"
    SIGNING_CHECK = "signing-check"
    PREPARE = "prepare"
    SIGN = "sign"
    INSTALL = "install"
    VERIFY = "verify"
    DONE = "done"
    FAILED = "failed"


ORDERED_STEPS: list[InstallStep] = [
    InstallStep.SELECT,
    InstallStep.ANALYZE,
    InstallStep.DETECT,
    InstallStep.SIGNING_CHECK,
    InstallStep.PREPARE,
    InstallStep.SIGN,
    InstallStep.INSTALL,
    InstallStep.VERIFY,
    InstallStep.DONE,
]

STEP_LABELS: dict[InstallStep, str] = {
    InstallStep.SELECT: "IPA loaded",
    InstallStep.ANALYZE: "IPA analyzed",
    InstallStep.DETECT: "iPhone connected",
    InstallStep.SIGNING_CHECK: "Signing requirements checked",
    InstallStep.PREPARE: "Installation prepared",
    InstallStep.SIGN: "Signing prepared",
    InstallStep.INSTALL: "Installing application",
    InstallStep.VERIFY: "Verified",
    InstallStep.DONE: "Installation complete",
    InstallStep.FAILED: "Installation failed",
}


@dataclass
class InstallationJob:
    ipa_path: str
    udid: str
    app_name: str = ""
    bundle_id: str = ""
    step: InstallStep = InstallStep.SELECT
    progress: float = 0.0  # 0..1 across whole workflow
    message: str = ""
    error_title: str = ""
    error_detail: str = ""
    log: list[str] = field(default_factory=list)

    def advance(self, step: InstallStep, progress: float, message: str = "") -> None:
        self.step = step
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.message = message
            self.log.append(f"[{step.value}] {message}")

    def fail(self, title: str, detail: str) -> None:
        self.step = InstallStep.FAILED
        self.error_title = title
        self.error_detail = detail
        self.log.append(f"[failed] {title}: {detail}")
