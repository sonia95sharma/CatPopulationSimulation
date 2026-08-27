"""
Biological constants for the cat population simulation.

SINGLE SOURCE OF TRUTH. Every fixed reproductive parameter used by the model is
defined here and imported by:
  - enhanced_simulation_ui.py  (Flask server)
  - working_simulation_adapter.py  (simulation engine)

Do NOT hardcode these values anywhere else. Values are drawn from peer-reviewed
literature; per-parameter sources are noted in the comments.
"""

# --- Estrous cycle (Shille, Lundstrom & Stabenfeldt 1979) ---
# Estrus duration 7.4 d (SD 3.7; range 2-19); interval between estrous periods
# 9.0 d (SD 7.6; range 4-22). Complete cycle 7.4 + 9.0 = 16.4 d, rounded for the
# 6-month-timestep model.
ESTRUS_LENGTH_DAYS = 7
ESTROUS_CYCLE_DAYS = 16

# --- Age at sexual maturity ---
# Females: mean 8.5 mo (SD 2.0; range 4-18) — Jemmett & Evans 1977; Festing &
# Bleby 1970 (as reviewed in Ng, Fascetti & Larsen 2023).
FEMALE_MATURITY_MEAN_MONTHS = 8.5
FEMALE_MATURITY_SD_MONTHS = 2.0
FEMALE_MATURITY_MIN_MONTHS = 4.0
FEMALE_MATURITY_MAX_MONTHS = 18.0
# Males: mean 10 mo (range 7-12) — Johnson 2022; Kutzler 2022; Pintus et al. 2021.
MALE_MATURITY_MEAN_MONTHS = 10.0
MALE_MATURITY_MIN_MONTHS = 7.0
MALE_MATURITY_MAX_MONTHS = 12.0

# --- Gestation & postpartum ---
# Gestation 65 d (Ng et al. 2023). Postpartum delay 8 weeks / 56 d
# (Wildt et al. 1981; Griffin 2001).
GESTATION_PERIOD_DAYS = 65
POSTPARTUM_DELAY_DAYS = 56

# --- Litter size (Fournier et al. 2017; Robinson & Cox 1970) ---
MEAN_LITTER_SIZE = 4.0
SD_LITTER_SIZE = 1.9
MIN_LITTER_SIZE = 1
MAX_LITTER_SIZE = 9

# --- Density-dependent kitten mortality ---
# Fraction of kittens that die before ~6 months. The engine interpolates from the
# base (low-density) rate up to the high-density rate as the population approaches
# carrying capacity. Calibrated so the model reproduces the unmanaged growth rate of
# Miller et al. 2014 (~18-20%/yr) and the sterilization response of Boone et al. 2019;
# these rates are within the high kitten mortality reported for free-roaming cats.
BASE_KITTEN_MORTALITY = 0.90           # at low density
HIGH_DENSITY_KITTEN_MORTALITY = 0.95   # at carrying capacity

# --- Breeding season (temperate; cats are seasonally polyestrous) ---
BREEDING_SEASON_START_MONTH = 1  # January
BREEDING_SEASON_END_MONTH = 9    # September

# --- Aggregate model proxy ---
# Fraction of each adult bucket treated as sexually mature breeders.
MATURE_FRACTION = 0.85

# Maturation lag, in 6-month timesteps: how long kittens remain non-breeding
# juveniles before entering the breeding population. Derived from the mean age at
# sexual maturity (~8.5 mo females / ~10 mo males) combined with the seasonal
# reality that kittens born in one breeding season generally do not breed until the
# next one. With 6-month timesteps a lag of 1 places first breeding at ~12 months.
MATURATION_LAG_TIMESTEPS = 1

# --- Breeding-day fractions (male-attention / crowding model) ---
# Share of days on which a female is observed mating. An intact female mates on
# relatively few days because she is pregnant/postpartum most of the time; an
# AMH-treated female never conceives, so she stays available and mates on more days.
# This difference in availability is what lets AMH females draw male attention away
# from fertile females. Values from the prepubertal AMH gene-therapy trial: treated
# females bred on ~34-47% of days vs ~15% for intact controls (PMC12663202).
INTACT_BREEDING_DAY_FRACTION = 0.15
AMH_BREEDING_DAY_FRACTION = 0.40

# --- Defaults for user-adjustable parameters (the UI normally supplies these;
#     these values are only used if a parameter is missing from the request). ---
DEFAULT_LITTERS_PER_YEAR = 2.0
DEFAULT_MALE_BREEDING_CAPACITY_PER_DAY = 3.0
DEFAULT_AMH_MONOPOLIZATION_DAYS = 15
DEFAULT_ADULT_MORTALITY_ANNUAL = 10.0
