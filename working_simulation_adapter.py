#!/usr/bin/env python3
"""
Simulation engine matching Boone et al. (2019) methodology
"""

import numpy as np
import random
from datetime import datetime, timedelta


def run_adapted_simulation(params):
    """
    Run cat population simulation matching the paper's approach

    Key aspects from paper:
    - Population starts AT carrying capacity
    - Density-dependent kitten mortality (75%-90%)
    - Adult mortality 10% annually
    - Seasonal breeding (not Oct-Dec)
    - TNR applied continuously (X% per timestep)
    """
    # Extract parameters
    years = params.get('simulation_years', 10)
    initial_pop = params.get('focal_population', 50)
    pct_spayed = params.get('pct_females_spayed', 0)
    pct_neutered = params.get('pct_males_neutered', 0)
    pct_amh = params.get('pct_females_amh', 0)
    mean_litter_size = params.get('mean_litter_size', 3.5)

    # Paper states population starts AT carrying capacity
    carrying_capacity = params.get('focal_carrying_capacity', initial_pop)

    # Determine scenario
    if pct_spayed > 0:
        scenario = 'spay'
        treatment_pct = pct_spayed
    elif pct_amh > 0:
        scenario = 'amh'
        treatment_pct = pct_amh
    else:
        scenario = 'none'
        treatment_pct = 0

    random.seed(42)

    # Initialize population
    females = int(initial_pop * 0.5)
    males = initial_pop - females

    # Initial treatment (only on starting population)
    treated_females = int(females * treatment_pct / 100)
    intact_females = females - treated_females

    # 6-month timestep tracking (matching paper's methodology)
    timesteps = years * 2  # 2 timesteps per year
    population = [initial_pop]
    focal_population_sizes = [initial_pop]
    neighborhood_population_sizes = [200]

    intact_female_count = [intact_females]
    treated_female_count = [treated_females]
    male_count = [males]
    pregnant_females_list = [0]
    estrus_females = [0]
    timestep_kittens = [0]

    # Biological parameters
    gestation_period = 1  # 6-month timesteps (pregnancy happens within timestep)
    postpartum_delay = 0  # Already accounted for in litters_per_year

    # Tracking
    total_births = 0
    total_kitten_deaths = 0

    # Simulate each 6-month timestep
    for timestep in range(1, timesteps + 1):
        current_date = datetime(2023, 1, 1) + timedelta(days=timestep * 182)
        breeding_season = current_date.month < 10  # Jan-Sep only

        # Current state
        current_pop = population[-1]
        current_intact_females = intact_female_count[-1]
        current_treated_females = treated_female_count[-1]
        current_males = male_count[-1]

        # CRITICAL: Calculate density for regulation
        density = current_pop / carrying_capacity

        # TNR: Continuous sterilization of NEW animals entering population
        # NOT re-sterilizing already sterilized animals
        # Only sterilize kittens that just matured (roughly treatment_pct of new matures)
        # This is handled implicitly - initial sterilization was done, no ongoing TNR

        # Mature breeding population (85% of adults are mature)
        mature_intact_females = current_intact_females * 0.85
        mature_treated_females = current_treated_females * 0.85
        mature_males = current_males * 0.85

        # Females in estrus (8 out of 21 days of cycle)
        estrus_count = 0
        if breeding_season:
            estrus_count = mature_intact_females * (8.0 / 21.0)

        # AMH MONOPOLIZATION EFFECT
        # AMH-treated females still cycle and monopolize males without getting pregnant
        # They are in estrus for ~15 days per 21-day cycle (longer than intact females)
        male_availability = 1.0  # Start with 100% male availability

        if scenario == 'amh' and breeding_season and mature_treated_females > 0:
            # AMH females monopolize males for 15/21 days vs intact females' 8/21 days
            amh_monopolization_ratio = 15.0 / 21.0  # ~71% of the time
            intact_estrus_ratio = 8.0 / 21.0  # ~38% of the time

            # Calculate competitive advantage: AMH females tie up males more
            # Reduce male availability based on ratio of AMH to intact females
            amh_to_intact_ratio = mature_treated_females / max(mature_intact_females, 1)
            male_reduction = amh_to_intact_ratio * (amh_monopolization_ratio / intact_estrus_ratio)
            male_availability = 1.0 / (1.0 + male_reduction * 0.5)  # Reduce by competition effect

        # Breeding in this 6-month timestep
        # Paper: litters_per_year parameter controls breeding rate
        # BUT not all females breed - only those in estrus and successfully mating
        litters_per_year = params.get('litters_per_year', 1.4)

        if breeding_season and mature_intact_females > 0 and mature_males > 0:
            # Number of litters per female in this 6-month period
            # Adjusted by male availability (reduced if AMH females monopolize males)
            kitten_count = mature_intact_females * (litters_per_year / 2.0) * mean_litter_size * male_availability
            total_births += kitten_count
        else:
            kitten_count = 0

        # CRITICAL: Density-dependent kitten mortality
        # Configurable parameters allow switching between scenarios:
        # - Boone 2019 (stable): base=75%, high=87%
        # - Miller 2014 (growing): base=60%, high=90%
        base_kitten_mortality = params.get('base_kitten_mortality', 0.75)
        high_density_mortality = params.get('high_density_mortality', 0.87)

        if density < 1.0:
            # Below capacity: interpolate from base to high
            mortality_range = high_density_mortality - base_kitten_mortality
            kitten_mortality = base_kitten_mortality + (density * mortality_range)
        else:
            # At or above capacity: use high density mortality
            kitten_mortality = high_density_mortality

        kitten_deaths = kitten_count * kitten_mortality
        total_kitten_deaths += kitten_deaths
        surviving_kittens = kitten_count - kitten_deaths

        # Adult mortality: 10% annually = 4.9% per 6 months
        timestep_adult_mortality = 1 - (0.90 ** (1.0/2.0))

        # Apply mortality to adults
        surviving_males = current_males * (1 - timestep_adult_mortality)
        surviving_intact_females = current_intact_females * (1 - timestep_adult_mortality)
        surviving_treated_females = current_treated_females * (1 - timestep_adult_mortality)

        # Add surviving kittens (split 50/50 male/female)
        # Apply TNR to new kittens
        new_female_kittens = surviving_kittens * 0.5
        if scenario != 'none' and treatment_pct > 0:
            newly_treated = new_female_kittens * (treatment_pct / 100.0)
            new_males = surviving_males + (surviving_kittens * 0.5) * (1 - treatment_pct / 100.0)  # Males also neutered
            new_intact_females = surviving_intact_females + (new_female_kittens - newly_treated)
            new_treated_females = surviving_treated_females + newly_treated
        else:
            new_males = surviving_males + (surviving_kittens * 0.5)
            new_intact_females = surviving_intact_females + new_female_kittens
            new_treated_females = surviving_treated_females

        # Calculate new population
        new_population = new_males + new_intact_females + new_treated_females

        # CRITICAL: Enforce carrying capacity
        # Paper assumes population STAYS at carrying capacity in baseline scenario
        # This is achieved through additional mortality/emigration when over capacity
        if new_population > carrying_capacity:
            # Apply additional density-dependent mortality to bring back to capacity
            excess = new_population - carrying_capacity
            # Remove excess proportionally from all groups
            scale = carrying_capacity / new_population
            new_males *= scale
            new_intact_females *= scale
            new_treated_females *= scale
            new_population = carrying_capacity

        # Record
        population.append(new_population)
        focal_population_sizes.append(new_population)
        neighborhood_population_sizes.append(200)
        male_count.append(new_males)
        intact_female_count.append(new_intact_females)
        treated_female_count.append(new_treated_females)
        pregnant_females_list.append(0)  # Not tracking pregnancies in 6-month model
        estrus_females.append(estrus_count)
        timestep_kittens.append(kitten_count)

    # Convert to daily sampling for visualization
    simulation_days = years * 365
    sample_interval = 30
    days = list(range(0, simulation_days, sample_interval))

    def interpolate_to_days(timestep_data):
        """Linearly interpolate between 6-month timesteps for smooth visualization"""
        daily_data = []
        for day in days:
            # Which timestep period are we in?
            timestep_float = day / 182.5  # 182.5 days per 6 months
            timestep_idx = int(timestep_float)

            # Handle edges
            if timestep_idx >= len(timestep_data) - 1:
                daily_data.append(timestep_data[-1])
            else:
                # Linear interpolation between timesteps
                fraction = timestep_float - timestep_idx
                value_start = timestep_data[timestep_idx]
                value_end = timestep_data[timestep_idx + 1]
                interpolated = value_start + (value_end - value_start) * fraction
                daily_data.append(interpolated)
        return daily_data

    # Calculate survival rate
    kittens_survived = total_births - total_kitten_deaths
    kitten_survival_rate = kittens_survived / total_births if total_births > 0 else 0

    return {
        'days': days,
        'focal_population_sizes': interpolate_to_days(focal_population_sizes),
        'neighborhood_population_sizes': interpolate_to_days(neighborhood_population_sizes),
        'population_sizes': interpolate_to_days(population),
        'females_in_estrus': interpolate_to_days(estrus_females),
        'pregnant_females': interpolate_to_days(pregnant_females_list),
        'males_monopolizing': [0] * len(days),  # Simplified
        'immigrants': [0] * len(days),
        'emigrants': [0] * len(days),
        'abandoned_kittens': [0] * len(days),
        'total_births': int(total_births),
        'total_deaths': int(total_kitten_deaths),
        'total_kitten_deaths': int(total_kitten_deaths),
        'total_immigrants': 0,
        'total_emigrants': 0,
        'total_abandoned': 0,
        'kitten_survival_rate': kitten_survival_rate,
    }
