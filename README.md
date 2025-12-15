# Cat Population Simulation

A web-based interactive simulator for modeling free-roaming cat population dynamics with configurable biological parameters and fertility control interventions.

## Overview

This simulation models cat populations using a 6-month timestep approach with density-dependent mortality, seasonal breeding, metapopulation dynamics, and various fertility control methods including surgical sterilization and contraception.

## Features

- **Interactive Web Interface**: Adjust all parameters via sliders and see real-time visualizations
- **Biological Realism**: Estrous cycles, seasonal breeding, gestation periods, and maturity ages
- **Multiple Fertility Control Methods**:
  - Surgical sterilization (spay/neuter)
  - AMH contraception
  - Comparative effectiveness analysis
- **Metapopulation Dynamics**: Focal (managed) and neighborhood (unmanaged) populations with dispersal
- **Density-Dependent Regulation**: Kitten mortality adjusts based on population density
- **Validation**: Tested against peer-reviewed scientific literature (Boone et al. 2019, Miller et al. 2014)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/populationSimulation.git
cd populationSimulation
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python enhanced_simulation_ui.py
```

4. Open your browser to:
```
http://localhost:5001
```

## Usage

### Running a Simulation

1. **Adjust Population Parameters**:
   - Focal population: The managed population where interventions occur
   - Neighborhood population: The unmanaged source of immigrants
   - Carrying capacities for both populations

2. **Configure Fertility Control**:
   - % of females surgically sterilized
   - % of females receiving AMH contraception
   - % of males neutered

3. **Set Biological Parameters**:
   - Estrous cycle length (default: 21 days)
   - Breeding season (default: January-September)
   - Litter size and frequency
   - Kitten mortality rates (density-dependent)

4. **Click "Run Simulation"** to generate results

### Understanding Results

The simulation produces four main visualizations:

1. **Population Over Time**: Shows focal vs. neighborhood populations
2. **Reproductive Status**: Tracks females in estrus and pregnant females
3. **Population Movement**: Immigration, emigration, and abandoned kittens
4. **Summary Statistics**: Total births, survival rates, and population changes

## Key Parameters

### Kitten Mortality (Density-Dependent)

The simulation uses density-dependent kitten mortality, which is critical for realistic population dynamics:

- **Base Kitten Mortality** (50-90%): Mortality rate at low population density
- **High Density Mortality** (70-95%): Mortality rate at/above carrying capacity

**Typical scenarios**:
- **Stable populations** (at carrying capacity): base=75%, high=87%
- **Growing populations** (resource-rich urban): base=55%, high=90%

### Breeding Parameters

- **Litters per year**: 1.4-2.0 (depends on environment)
- **Mean litter size**: 3.5-4.0 kittens
- **Breeding season**: January-September (no breeding October-December)
- **Estrous cycle**: 21 days (8 days in estrus)

### Maturity Ages

- **Female maturity**: 6-8 months
- **Male maturity**: 12 months

### Population Dynamics

- **Adult mortality**: 10% annually (constant across ages)
- **Dispersal rate**: 2% per 6 months (between populations)
- **Immigration rate**: 2% per 6 months (from neighborhood to focal)

## Validation

The simulation has been validated against two major scientific studies:

### Boone et al. (2019) - Frontiers in Veterinary Science

**Accuracy**: ~85% match on final population sizes

Validated scenarios:
- Baseline (no management): 50 → 48 cats (expected: 50)
- 25% sterilization: 50 → 39 cats (expected: 42)
- 75% sterilization: 50 → 18 cats (expected: 21)

### Miller et al. (2014) - PLOS ONE

**Accuracy**: ~95% match on growth rates

Validated scenarios:
- Large Urban (no management): 17.9% annual growth (expected: 18-20%)
- Treatment thresholds for population decline
- Impact of demographic connectivity

See `VALIDATION_REPORT_MILLER_2014.md` for detailed validation results.

## Technical Architecture

### Core Components

1. **enhanced_simulation_ui.py**: Flask web server and API endpoints
2. **working_simulation_adapter.py**: Core simulation engine (6-month timesteps)
3. **biological_parameters.py**: Default parameter configurations
4. **templates/enhanced_index.html**: Interactive web interface

### Simulation Methodology

- **Timestep**: 6 months (matching scientific literature)
- **Demographic processes**: Birth, death, maturity, migration
- **Density regulation**: Via kitten mortality curve
- **Carrying capacity**: Hard ceiling with proportional mortality when exceeded

## Validation Scripts

Two automated validation scripts are included:

```bash
# Validate against both papers
python automated_paper_validation.py

# Validate against Miller 2014 specifically
python validate_miller_2014.py
```

## File Structure

```
populationSimulation/
├── enhanced_simulation_ui.py          # Flask web server
├── working_simulation_adapter.py      # Simulation engine
├── biological_parameters.py           # Default parameters
├── automated_paper_validation.py      # Validation script
├── validate_miller_2014.py           # Miller 2014 validation
├── VALIDATION_REPORT_MILLER_2014.md  # Validation documentation
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── templates/
│   └── enhanced_index.html           # Web interface
└── .gitignore                        # Git ignore rules
```

## Disclaimer

⚠️ **Important**: This simulator is a simplified model intended for educational and exploratory purposes only. It does not capture all real-world variables and should not be used for policy decisions, medical or veterinary guidance, or other high-stakes planning.

The simulation makes several simplifying assumptions:
- Deterministic rather than stochastic (single run vs. 1,000 iterations)
- Simplified mating dynamics
- Homogeneous population (no age structure beyond mature/immature)
- Constant adult mortality (not density-dependent)
- No disease, predation, or other external factors

## References

1. Boone, J. D., Miller, P. S., Briggs, J. R., et al. (2019). A Long-Term Lens: Cumulative Impacts of Free-Roaming Cat Management Strategy and Intensity on Preventable Cat Mortalities. *Frontiers in Veterinary Science* 6:238.

2. Miller, P. S., Boone, J. D., Briggs, J. R., et al. (2014). Simulating Free-Roaming Cat Population Management Options in Open Demographic Environments. *PLOS ONE* 9(11): e113553.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Contact

For questions or feedback, please open an issue on GitHub.

## Acknowledgments

This simulation was developed based on methodology from peer-reviewed scientific literature on free-roaming cat population dynamics. Special thanks to the researchers who made their methods publicly available for validation and replication.
