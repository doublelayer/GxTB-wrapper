from ase.build import molecule
from ase_gxtb import GXTB

atoms = molecule("H2")
atoms.calc = GXTB(charge=0, uhf=0)

energy  = atoms.get_potential_energy()
forces  = atoms.get_forces()
charges = atoms.calc.get_charges()

print(f"H2  energy  : {energy:.6f}")
print(f"H2  forces  :\n{forces}")
print(f"H2  charges : {charges}")
