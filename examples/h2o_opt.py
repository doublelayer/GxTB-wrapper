from ase.build import molecule
from ase.optimize import BFGS
from ase_gxtb import GXTB

atoms = molecule("H2O")
atoms.calc = GXTB(charge=0, uhf=0, keep_files=False)

opt = BFGS(atoms, trajectory="h2o_opt.traj", logfile="h2o_opt.log")
opt.run(fmax=0.01)

atoms.write("h2o_opt.xyz")

energy  = atoms.get_potential_energy()
forces  = atoms.get_forces()
charges = atoms.calc.get_charges()

print(f"H2O  optimized energy : {energy:.6f}")
print(f"H2O  forces           :\n{forces}")
print(f"H2O  charges          : {charges}")
