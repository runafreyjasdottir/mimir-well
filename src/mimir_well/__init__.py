"""
Mímir's Well — AI Memory Database
===================================
Persistent, self-healing memory with Ebbinghaus decay, FTS5 search,
contradiction detection, and knowledge promotion.

ᛗ í ᛗ í ᚱ — From the Well, all wisdom flows.
"""

__version__ = "2.0.0"
__author__ = "Eldrä Járnsdóttir"
__description__ = "AI Memory Database with Ebbinghaus Decay and Self-Healing"

from mimir_well.core import RunaMemory
from mimir_well.config import MimirConfig
from mimir_well.decay import (
    compute_ebbinghaus_decay,
    compute_reinforcement_boost,
    compute_confidence_for_promotion,
    should_decay,
    should_promote,
)
from mimir_well.repair import check_integrity, repair_database
from mimir_well.backup import (
    backup_database,
    backup_with_rotation,
    restore_from_backup,
    export_to_json,
)

__all__ = [
    "RunaMemory",
    "MimirConfig",
    "compute_ebbinghaus_decay",
    "compute_reinforcement_boost",
    "compute_confidence_for_promotion",
    "should_decay",
    "should_promote",
    "check_integrity",
    "repair_database",
    "backup_database",
    "backup_with_rotation",
    "restore_from_backup",
    "export_to_json",
]