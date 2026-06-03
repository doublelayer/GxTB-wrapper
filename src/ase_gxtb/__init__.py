"""
ase-gxtb: ASE calculator wrapper for the GxTB semiempirical binary.

The GxTB binary is developed by the Grimme group and installed automatically
into your environment when you run ``pip install .``.

Basic usage::

    from ase_gxtb import GXTB
    from ase.build import molecule

    atoms = molecule("H2O")
    atoms.calc = GXTB(charge=0, uhf=0)

    energy  = atoms.get_potential_energy()
    forces  = atoms.get_forces()
    charges = atoms.calc.get_charges() or atoms.get_charges() 
"""

from ase_gxtb.calculator import GXTB

__version__ = "0.1.0"
__all__ = ["GXTB"]
