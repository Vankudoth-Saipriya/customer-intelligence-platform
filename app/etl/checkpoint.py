"""
Pipeline Checkpoint Manager for tracking and restoring ETL execution state.

Persists pipeline progress as JSON artifacts in artifacts/checkpoints/ to support
resuming interrupted batch execution.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from loguru import logger

from app.etl.utils.dataset_types import DatasetType


@dataclass
class DatasetCheckpoint:
    """
    Checkpoint record tracking a single dataset's pipeline state.
    """

    dataset: str
    current_stage: str
    completion_status: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class PipelineCheckpointState:
    """
    Persisted pipeline checkpoint state tracking all completed dataset progress.
    """

    completed_datasets: List[str] = field(default_factory=list)
    failed_dataset: Optional[str] = None
    last_stage: Optional[str] = None
    dataset_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class CheckpointManager:
    """
    Manages persistent JSON pipeline checkpoints in artifacts/checkpoints/.
    """

    def __init__(self, checkpoint_dir: Optional[Path] = None) -> None:
        """
        Initialize CheckpointManager with output directory.

        Args:
            checkpoint_dir: Directory path for JSON checkpoints. Defaults to artifacts/checkpoints/.
        """
        if checkpoint_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self.checkpoint_dir = project_root / "artifacts" / "checkpoints"
        else:
            self.checkpoint_dir = Path(checkpoint_dir)

        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"

    def _ensure_dir(self) -> None:
        """
        Ensure checkpoint directory exists on filesystem.
        """
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        completed_datasets: List[Union[DatasetType, str]],
        current_dataset: Optional[Union[DatasetType, str]] = None,
        stage: str = "COMPLETED",
        status: str = "SUCCESS",
    ) -> None:
        """
        Save current pipeline progress checkpoint to JSON file.

        Args:
            completed_datasets: List of completed dataset identifiers.
            current_dataset: Dataset currently being processed.
            stage: Current pipeline stage name.
            status: Stage status (e.g. SUCCESS, FAILED).
        """
        self._ensure_dir()
        completed_names = [
            d.value if isinstance(d, DatasetType) else str(d)
            for d in completed_datasets
        ]
        curr_name = (
            current_dataset.value
            if isinstance(current_dataset, DatasetType)
            else (str(current_dataset) if current_dataset else None)
        )

        state = PipelineCheckpointState(
            completed_datasets=completed_names,
            failed_dataset=curr_name if status == "FAILED" else None,
            last_stage=stage,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2)

        logger.info(
            f"Checkpoint created/updated: {len(completed_names)} completed datasets ({completed_names}) saved to '{self.checkpoint_file}'"
        )

    def load_checkpoint(self) -> Optional[PipelineCheckpointState]:
        """
        Load latest pipeline checkpoint from JSON file if present.

        Returns:
            PipelineCheckpointState if checkpoint exists and is valid, else None.
        """
        if not self.checkpoint_file.exists():
            logger.info("No existing pipeline checkpoint detected.")
            return None

        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            state = PipelineCheckpointState(**data)
            logger.info(
                f"Restored pipeline checkpoint: {len(state.completed_datasets)} completed datasets ({state.completed_datasets}) from '{self.checkpoint_file}'"
            )
            return state
        except Exception as exc:
            logger.warning(
                f"Failed to load checkpoint file '{self.checkpoint_file}': {str(exc)}. Proceeding with full execution."
            )
            return None

    def clear_checkpoint(self) -> None:
        """
        Remove checkpoint JSON file after a successful full pipeline run.
        """
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                logger.info(
                    f"Automatically removed checkpoint file after successful full pipeline run: '{self.checkpoint_file}'"
                )
            except Exception as exc:
                logger.warning(
                    f"Failed to delete checkpoint file '{self.checkpoint_file}': {str(exc)}"
                )
