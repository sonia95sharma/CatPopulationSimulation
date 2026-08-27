# Cat Population Simulation

A web-based interactive simulator for modeling free-roaming cat population dynamics and comparing reproductive-management strategies — surgical sterilization, AMH-based contraception, or a combination of both.

## Overview

This simulation models cat populations using a 6-month timestep approach with a maturation delay, density-dependent kitten mortality, seasonal breeding, a male-attention mating model, and open-population dynamics (arrivals and departures). It can be run as a single deterministic trajectory or as a stochastic ensemble that produces confidence bands and a probability of near-eradication.

## Features

- **Interactive web interface**: adjust management parameters via sliders and see real-time visualizations.
- **Three interventions, combinable**: surgical spaying (females), neutering (males), and AMH contraception (females) — any mix can be applied in a single run.
- **Two intervention schedules**: *one-time* (applied once to the initial population; coverage then decays as treated cats die) or *yearly* (re-applied to the current intact population each year).
- **Percentage or absolute numbers**: express coverage as a % of the population, or as a fixed number of animals per intervention (e.g., "40 females/year"). Absolute maxima scale to the population size.
- **AMH crowding-out effect**: AMH-treated females still cycle and draw male attention (but cannot conceive), which can reduce mating opportunities for fertile females — a population-level effect specific to contraception that spaying does not produce.
- **Maturation delay**: kittens enter a juvenile stage and cannot breed until they mature (~12 months), based on the literature ages at sexual maturity.
- **Density-dependent regulation**: kitten mortality rises with density toward carrying capacity; carrying capacity can be enabled (a ceiling) or disabled (unbounded growth).
- **Stochastic mode**: run many simulations to get a mean trajectory, a 90% confidence band, and the probability of near-eradication.
- **Save & compare**: name runs, compare them side by side, and export a comparison to CSV.
- **Assumptions page**: every fixed biological value and its literature source is listed at `/assumptions`.
- **Validation**: calibrated against peer-reviewed literature (Boone et al. 2019, Miller et al. 2014).

## Installation

### Prerequisites

- Python 3.8+ and pip

### Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python enhanced_simulation_ui.py
```

3. Open your browser to:
```
http://localhost:5001
```

## Usage

1. **Set population structure**: initial adult population, sex ratio (male %), and carrying capacity (or disable it for unbounded growth).
2. **Set population dynamics**: annual adult mortality, and yearly arrivals (intact immigrants/abandonments) and departures/removals.
3. **Set breeding parameters**: average litters per year, and male breeding capacity.
4. **Configure fertility control**: choose percentage or absolute numbers, one-time or yearly, then set AMH / spay / neuter levels.
5. **(Optional) number of simulations** (1 = deterministic; more = stochastic ensemble).
6. **Click "Run Enhanced Simulation"**, then optionally name the run and **Save for Comparison**.

## Fixed biological parameters

These values are not user-adjustable and are defined in one place (`biological_parameters.py`). The live list with full citations is available in the app at **`/assumptions`**.

| Parameter | Value | Source (summary) |
|---|---|---|
| Estrous cycle | 16 days (7-day estrus + ~9-day interval) | Shille et al. 1979 |
| Female sexual maturity | 8.5 months (SD 2.0; range 4–18) | Jemmett & Evans 1977; Festing & Bleby 1970 |
| Male sexual maturity | 10 months (range 7–12) | Johnson 2022; Kutzler 2022; Pintus et al. 2021 |
| Gestation | 65 days | Ng et al. 2023 |
| Postpartum delay | 56 days (8 weeks) | Wildt et al. 1981; Griffin 2001 |
| Mean litter size | 4.0 (SD 1.9; range 1–9) | Fournier et al. 2017; Robinson & Cox 1970 |
| Kitten mortality | 90% (low density) → 95% (at capacity) | Calibrated to Miller 2014 / Boone 2019 |
| Breeding season | January–September | Seasonally polyestrous (temperate) |

Adjustable parameters (litters/year, male breeding capacity, adult mortality, population sizes, arrivals/departures, interventions, number of simulations) are set in the interface.

## Key modeling notes

- **Timestep**: 6 months. Realized litters over a year always equal the "litters per year" setting; the breeding season governs *when* litters occur, not *how many*.
- **Reproductive ceiling**: gestation + postpartum + return-to-estrus caps the maximum litters/year a queen can achieve (~2.83), so requests above that are trimmed.
- **Male-attention mating model**: intact males have a limited number of matings per day; intact and AMH females compete for that attention, while spayed females do not cycle and create no demand.
- **Density regulation** is carried mainly by kitten survival; adult mortality is applied at a constant annual rate.

## Validation

The model reproduces the broad behavior of two studies (re-validated after recalibration):

### Boone et al. (2019) — *Frontiers in Veterinary Science*
Starting at carrying capacity (50), closed population, 10 years:

| Scenario | Model | Paper |
|---|---|---|
| Baseline (no management) | 50 | ~50 |
| 25% spayed (yearly) | 35 | ~42 |
| 75% spayed (yearly) | 20 | ~21 |

### Miller et al. (2014) — *PLOS ONE*
Unmanaged, open/uncapped population:

| | Model | Paper |
|---|---|---|
| Annual growth rate | ~20.5%/yr | 18–20% |

*Note:* the 25%-sterilization case suppresses slightly more than Boone reports; this is sensitive to the exact trapping protocol (one-time vs sustained, both-sex vs female-only), which the paper models in more detail than this exploratory tool.

## Technical architecture

- **`enhanced_simulation_ui.py`** — Flask web server, plotting, save/compare/export, and the `/assumptions` page.
- **`working_simulation_adapter.py`** — the simulation engine (6-month timesteps; deterministic run and stochastic ensemble).
- **`biological_parameters.py`** — the single source of truth for all fixed biological constants.
- **`templates/enhanced_index.html`** — the interactive interface.
- **`templates/assumptions.html`** — the assumed-values / sources page.

## Disclaimer

⚠️ **Important**: This simulator is a simplified model intended for educational and exploratory purposes only. It does not capture all real-world variables and should not be used for policy decisions, medical or veterinary guidance, or other high-stakes planning.

Simplifying assumptions include:
- Coarse 6-month timesteps and a single juvenile stage rather than full age structure.
- Adult mortality is constant (not density-dependent or sex/status-specific).
- A heuristic male-attention mating model rather than mechanistic mate choice.
- AMH contraception is modeled as permanent (no waning) and identical in efficacy across individuals.
- No disease, predation, or other external factors.

## References

1. Boone, J. D., Miller, P. S., Briggs, J. R., et al. (2019). A Long-Term Lens: Cumulative Impacts of Free-Roaming Cat Management Strategy and Intensity on Preventable Cat Mortalities. *Frontiers in Veterinary Science* 6:238.
2. Miller, P. S., Boone, J. D., Briggs, J. R., et al. (2014). Simulating Free-Roaming Cat Population Management Options in Open Demographic Environments. *PLOS ONE* 9(11): e113553.

Additional sources for the fixed biological parameters are listed on the `/assumptions` page.

## License

MIT License — see LICENSE file for details.
