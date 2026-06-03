"""
calculator.py — ASE Calculator wrapper for the GxTB binary.

xtb runs in a numbered sp_XXXX subdirectory of the current working
directory, writing its output files (struc.engrad, charges, xtb.out, ...)
there — one directory per single-point call.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import numpy as np
from ase import Atoms
from ase.calculators.calculator import Calculator, all_changes
from ase.units import Bohr
from ase_gxtb.binary import ensure_gxtb_binary
from ase_gxtb.parser import parse_engrad, parse_charges

log = logging.getLogger(__name__)


class GXTBCalculationError(RuntimeError):
    """Raised when the xtb subprocess fails or output cannot be parsed."""


class GXTB(Calculator):
    """ASE Calculator that drives the GxTB binary via subprocess.

    Each calculate() call runs xtb in a numbered subdirectory
    sp_0000/, sp_0001/, ... of the current working directory.
    The caller is responsible for os.chdir() to the desired trial
    directory before running the optimisation.

    Parameters
    ----------
    charge : int
        Total charge of the system (default 0).
    uhf : int
        Number of unpaired electrons, passed as ``--uhf`` (default 0).
    maxiter : int
        Maximum SCF iterations, passed as ``--iterations`` (default 250).
    keep_files : bool
        Keep sp_XXXX directories after each calculation (default True).
        Set to False to delete them immediately after parsing, saving disk
        space during long optimisations.
    binary_path : str or Path or None
        Explicit path to the xtb binary. Overrides the automatic lookup.
    """

    implemented_properties: List[str] = ["energy", "forces", "charges"]

    default_parameters = dict(
        charge=0,
        uhf=0,
        maxiter=250,
        keep_files=True,
        binary_path=None,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._binary: Optional[Path] = None
        self._sp_counter = 0

    # ── public ────────────────────────────────────────────────────────────────

    def get_charges(self) -> np.ndarray:
        """Per-atom charges, shape (N,)."""
        return self.results["charges"]

    # ── ASE interface ─────────────────────────────────────────────────────────

    def calculate(
        self,
        atoms: Optional[Atoms] = None,
        properties: List[str] = None,
        system_changes: List[str] = all_changes,
    ) -> None:
        if properties is None:
            properties = self.implemented_properties
        super().calculate(atoms, properties, system_changes)
        sp_dir = Path.cwd() / f"sp_{self._sp_counter:04d}"
        self._sp_counter += 1
        sp_dir.mkdir(parents=True, exist_ok=True)
        self._run_in(sp_dir, self._resolve_binary())
        if not self.parameters.keep_files:
            shutil.rmtree(sp_dir, ignore_errors=True)

    # ── internal ──────────────────────────────────────────────────────────────

    def _resolve_binary(self) -> Path:
        if self.parameters.binary_path is not None:
            return Path(self.parameters.binary_path)
        if self._binary is None:
            self._binary = ensure_gxtb_binary()
        return self._binary

    def _run_in(self, work_dir: Path, binary_path: Path) -> None:
        atoms     = self.atoms
        engrad    = work_dir / "struc.engrad"
        charges_f = work_dir / "charges"
        log_path  = work_dir / "xtb.out"

        _write_coord(atoms, work_dir / "struc.coord")

        cmd = [
            str(binary_path),
            "struc.coord",
            "--gxtb",
            "--grad",
            "--chrg", str(self.parameters.charge),
            "--uhf",  str(self.parameters.uhf),
            "--iterations", str(self.parameters.maxiter),
        ]

        log.debug("xtb command: %s", " ".join(cmd))

        with open(log_path, "w") as fout:
            result = subprocess.run(
                cmd, cwd=work_dir,
                stdout=fout,
                stderr=subprocess.STDOUT,
            )

        if result.returncode != 0:
            raise GXTBCalculationError(
                f"xtb exited with return code {result.returncode} "
                f"in {work_dir}\n{log_path.read_text()}"
            )

        if not engrad.is_file():
            raise GXTBCalculationError(
                f"xtb exited rc=0 but struc.engrad was not created "
                f"in {work_dir}\n{log_path.read_text()}"
            )

        energy, forces = parse_engrad(engrad, len(atoms))
        charges = parse_charges(charges_f) if charges_f.is_file() else np.zeros(len(atoms))

        self.results["energy"]  = energy
        self.results["forces"]  = forces
        self.results["charges"] = charges
        self.atoms.arrays["charges"] = charges
        
def _write_xyz(atoms: Atoms, path: Path) -> None:
    symbols   = atoms.get_chemical_symbols()
    positions = atoms.get_positions()
    lines = [str(len(atoms)), "ase-gxtb input"]
    for sym, (x, y, z) in zip(symbols, positions):
        lines.append(f"{sym:2s}  {x:20.10f}  {y:20.10f}  {z:20.10f}")
    path.write_text("\n".join(lines) + "\n")

def _write_coord(atoms: Atoms, path: Path) -> None:
    symbols = atoms.get_chemical_symbols()
    positions_bohr = atoms.get_positions() / Bohr
    cell_bohr = atoms.get_cell().array / Bohr
    pbc = atoms.get_pbc()
    periodicity = int(sum(pbc))
    lines = ["$coord"]
    for sym, (x, y, z) in zip(symbols, positions_bohr):
        lines.append(f"  {x:20.10f}  {y:20.10f}  {z:20.10f}  {sym}")
    if periodicity > 0:
        lines.append(f"$periodic {periodicity}")
        lines.append("$lattice")
        for vector in cell_bohr:
            x, y, z = vector
            lines.append(f"  {x:20.10f}  {y:20.10f}  {z:20.10f}")
    lines.append("$end")
    path.write_text("\n".join(lines) + "\n")
