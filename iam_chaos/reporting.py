"""Machine-readable offline reports and artifact writers."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class OfflineReport:
    schema_version: str
    scenario: Dict[str, Any]
    seed: Any
    seed_hash: str
    payloads: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    assertions: List[Dict[str, Any]]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scenario": self.scenario,
            "seed": self.seed,
            "seed_hash": self.seed_hash,
            "payloads": self.payloads,
            "events": self.events,
            "assertions": self.assertions,
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
            sort_keys=True,
        )

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json() + "\n", encoding="utf-8")


def write_artifacts(report: OfflineReport, output_dir: Path) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "payloads": output_dir / "payloads.json",
        "events": output_dir / "events.json",
        "report": output_dir / "report.json",
    }
    paths["payloads"].write_text(
        json.dumps(
            report.payloads,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["events"].write_text(
        json.dumps(
            report.events,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    report.write_json(paths["report"])
    return paths
