"""
parser.py — parse GxTB / xTB output files.

With --gxtb --grad and input file struc.xyz, xtb writes:
  - struc.engrad  : energy (Eh) + gradient (Eh/Bohr), one component per line
  - charges       : per-atom partial charges, one float per line

Units are converted to ASE convention (eV, Å) using ase.units.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from ase.units import Bohr, Hartree


def parse_engrad(path: Path, n_atoms: int) -> tuple[float, np.ndarray]:
    """Parse ``struc.engrad``.

    Returns
    -------
    energy : float
        Total energy in eV.
    forces : np.ndarray, shape (N, 3)
        Cartesian forces in eV/Å  (forces = -gradient).
    """
    lines = [
        ln.strip()
        for ln in Path(path).read_text().splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]

    if len(lines) < 2 + 3 * n_atoms:
        raise ParseError(
            f"struc.engrad at {path} is too short "
            f"(expected at least {2 + 3 * n_atoms} data lines, got {len(lines)})"
        )

    try:
        natoms_file = int(lines[0])
    except ValueError as exc:
        raise ParseError(f"Cannot read natoms from {path}: {lines[0]!r}") from exc

    if natoms_file != n_atoms:
        raise ParseError(
            f"natoms mismatch in {path}: file says {natoms_file}, atoms object has {n_atoms}"
        )

    try:
        energy_eh = float(lines[1])
    except ValueError as exc:
        raise ParseError(f"Cannot read energy from {path}: {lines[1]!r}") from exc

    try:
        gradient = np.array([float(lines[2 + i]) for i in range(3 * n_atoms)])
    except ValueError as exc:
        raise ParseError(f"Cannot parse gradient in {path}: {exc}") from exc

    energy = energy_eh * Hartree
    forces = -gradient.reshape(n_atoms, 3) * (Hartree / Bohr)

    return energy, forces


def parse_charges(path: Path) -> np.ndarray:
    """Parse ``charges`` file (one float per line), return shape (N,)."""
    lines = [ln.strip() for ln in Path(path).read_text().splitlines() if ln.strip()]
    if not lines:
        raise ParseError(f"charges file at {path} is empty.")
    try:
        return np.array([float(ln) for ln in lines])
    except ValueError as exc:
        raise ParseError(f"Cannot parse charges file at {path}: {exc}") from exc


class ParseError(ValueError):
    """Raised when an xTB output file cannot be parsed."""
