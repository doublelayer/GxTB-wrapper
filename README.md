# ASE Wrapper for g-xTB

ASE calculator wrapper for the development version of [g-xTB](https://github.com/grimme-lab/g-xtb).

## Installation

```bash
git clone https://github.com/doublelayer/GxTB-wrapper
cd ase-gxtb
pip install .
```

The `xtb` binary (`6.7.1-gxtb-140526`) is downloaded and installed into the
environment's `bin/` directory automatically during `pip install`.  Nothing is
written outside the environment.

### Binary gxtb path override

```bash
export GXTB_BINARY=/path/to/xtb
```

## Usage
```
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
```

## API

```python
GXTB(
    charge=0,            # total charge
    uhf=0,               # unpaired electrons (xtb --uhf)
    maxiter=250,         # SCF iterations
    keep_files=False,    # keep workdir after calculation (debugging)
    extra_args=(),       # extra args passed to xtb
)
```

| Property | Method | Unit |
|---|---|---|
| Total energy | `atoms.get_potential_energy()` | eV |
| Cartesian forces | `atoms.get_forces()` | eV/Å |
| Per-atom charges | `atoms.calc.get_charges() \ atoms.get_charges()` | elementary charge (e) |

## License

`ase-gxtb` wrapper: MIT.  
GxTB binary: Grimme group license — see https://github.com/grimme-lab/g-xtb.

## Reference

- T. Froitzheim, M. Müller, A. Hansen, S. Grimme, g-xTB: A General-Purpose Extended Tight-Binding Electronic Structure Method For the Elements H to Lr (Z=1–103), (2025). https://doi.org/10.26434/chemrxiv-2025-bjxvt.
