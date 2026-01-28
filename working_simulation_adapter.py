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

    # Fertility control options
    fc_timing = params.get('fc_timing', 'one-time')  # 'one-time' or 'yearly'
    fc_unit = params.get('fc_unit', 'percentage')  # 'percentage' or 'absolute'
    fc_females_amh_absolute = params.get('fc_females_amh_absolute', 0)
    fc_females_spayed_absolute = params.get('fc_females_spayed_absolute', 0)
    fc_males_neutered_absolute = params.get('fc_males_neutered_absolute', 0)

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

    # Initialize population with adjustable sex ratio
    male_percentage = params.get('male_percentage', 50) / 100.0
    males = int(initial_pop * male_percentage)
    females = initial_pop - males

    # Initial treatment (only on starting population)
    if fc_timing == 'one-time':
        # One-time treatment at start
        treated_females = int(females * treatment_pct / 100)
        intact_females = females - treated_females
        neutered_males = int(males * pct_neutered / 100)
        intact_males = males - neutered_males
    else:
        # Yearly treatment starts after year 1
        treated_females = 0
        intact_females = females
        neutered_males = 0
        intact_males = males

    # 6-month timestep tracking (matching paper's methodology)
    timesteps = years * 2  # 2 timesteps per year
    population = [initial_pop]
    focal_population_sizes = [initial_pop]

    intact_female_count = [intact_females]
    treated_female_count = [treated_females]
    intact_male_count = [intact_males]
    neutered_male_count = [neutered_males]
    male_count = [males]
    pregnant_females_list = [0]
    estrus_females = [0]
    timestep_kittens = [0]
    arrivals_list = [0]
    departures_list = [0]

    # Biological parameters
    gestation_period = 1  # 6-month timesteps (pregnancy happens within timestep)
    postpartum_delay = 0  # Already accounted for in litters_per_year

    # Population dynamics parameters
    arrivals_per_year = params.get('arrivals_per_year', 10)
    departures_per_year = params.get('departures_per_year', 10)
    arrivals_per_6months = arrivals_per_year / 2.0  # Convert to per timestep
    departures_per_6months = departures_per_year / 2.0

    # Tracking
    total_births = 0
    total_kitten_deaths = 0
    total_arrivals = 0
    total_departures = 0

    # Simulate each 6-month timestep
    for timestep in range(1, timesteps + 1):
        current_date = datetime(2023, 1, 1) + timedelta(days=timestep * 182)
        breeding_season = current_date.month < 10  # Jan-Sep only

        # Current state
        current_pop = population[-1]
        current_intact_females = intact_female_count[-1]
        current_treated_females = treated_female_count[-1]
        current_intact_males = intact_male_count[-1]
        current_neutered_males = neutered_male_count[-1]
        current_males = male_count[-1]

        # Apply yearly fertility control interventions
        if fc_timing == 'yearly' and timestep % 2 == 0:  # Every year (every 2 timesteps)
            # Apply interventions to current population
            if fc_unit == 'absolute':
                # Treat a fixed number of animals per year
                females_to_treat = min(fc_females_amh_absolute + fc_females_spayed_absolute, current_intact_females)
                males_to_neuter = min(fc_males_neutered_absolute, current_intact_males)

                # Distribute treatments
                if scenario == 'amh' and fc_females_amh_absolute > 0:
                    newly_treated_amh = min(fc_females_amh_absolute, current_intact_females)
                    current_treated_females += newly_treated_amh
                    current_intact_females -= newly_treated_amh
                elif scenario == 'spay' and fc_females_spayed_absolute > 0:
                    newly_spayed = min(fc_females_spayed_absolute, current_intact_females)
                    current_treated_females += newly_spayed
                    current_intact_females -= newly_spayed

                if fc_males_neutered_absolute > 0:
                    newly_neutered = min(fc_males_neutered_absolute, current_intact_males)
                    current_neutered_males += newly_neutered
                    current_intact_males -= newly_neutered
            else:
                # Treat a percentage of current population
                if scenario == 'amh' and pct_amh > 0:
                    newly_treated_amh = int(current_intact_females * (pct_amh / 100))
                    current_treated_females += newly_treated_amh
                    current_intact_females -= newly_treated_amh
                elif scenario == 'spay' and pct_spayed > 0:
                    newly_spayed = int(current_intact_females * (pct_spayed / 100))
                    current_treated_females += newly_spayed
                    current_intact_females -= newly_spayed

                if pct_neutered > 0:
                    newly_neutered = int(current_intact_males * (pct_neutered / 100))
                    current_neutered_males += newly_neutered
                    current_intact_males -= newly_neutered

            # Update total males
            current_males = current_intact_males + current_neutered_males

        # CRITICAL: Calculate density for regulation
        density = current_pop / carrying_capacity

        # TNR: Continuous sterilization of NEW animals entering population
        # NOT re-sterilizing already sterilized animals
        # Only sterilize kittens that just matured (roughly treatment_pct of new matures)
        # This is handled implicitly - initial sterilization was done, no ongoing TNR

        # Mature breeding population (85% of adults are mature)
        mature_intact_females = current_intact_females * 0.85
        mature_treated_females = current_treated_females * 0.85
        mature_intact_males = current_intact_males * 0.85  # Only intact males can breed
        mature_males = current_males * 0.85  # For legacy compatibility

        # NEW MALE ATTENTION-BASED BREEDING MODEL
        # Males have limited breeding capacity: X females per male per day
        # Default: 3 females per male per day
        male_breeding_capacity_per_day = params.get('male_breeding_capacity_per_day', 3.0)

        # Hardcoded biological parameters
        estrus_length_days = 7  # From research data: avg 7.4 days
        estrous_cycle_days = 16  # From research data: 7.4 (estrus) + 9.0 (interval) = 16.4 days

        # Calculate total male breeding capacity over 6 months (182.5 days)
        days_in_timestep = 182.5
        breeding_season_days = days_in_timestep if breeding_season else 0

        # Total male*female*day capacity available (only intact males breed)
        total_male_capacity = mature_intact_males * male_breeding_capacity_per_day * breeding_season_days

        # Females in estrus (7 out of 9 days of cycle for intact females)
        estrus_ratio_intact = estrus_length_days / estrous_cycle_days
        estrus_count = 0
        if breeding_season:
            estrus_count = mature_intact_females * estrus_ratio_intact

        # Calculate female*day demand from different groups
        # Intact females: cycle 7 out of every 9 days
        intact_female_days_demand = mature_intact_females * estrus_ratio_intact * breeding_season_days

        # AMH females: also cycle but don't get pregnant (they monopolize male attention)
        # AMH females have extended estrus-like behavior
        amh_monopolization_days = params.get('monopolization_amh_days', 15)
        amh_cycle_ratio = min(amh_monopolization_days / estrous_cycle_days, 1.0)  # Proportion of time in estrus-like state
        amh_female_days_demand = mature_treated_females * amh_cycle_ratio * breeding_season_days if scenario == 'amh' else 0

        # Spayed females: do not cycle, no male attention demand
        spayed_female_days_demand = 0

        # Total female*day demand
        total_female_demand = intact_female_days_demand + amh_female_days_demand

        # Calculate breeding success rate based on supply/demand
        if total_female_demand > 0 and total_male_capacity > 0:
            # If demand exceeds supply, only a fraction of females get pregnant
            breeding_success_ratio = min(1.0, total_male_capacity / total_female_demand)

            # Only intact females can get pregnant (AMH females monopolize but don't conceive)
            # Calculate what fraction of intact females' demand is met
            if total_female_demand > total_male_capacity:
                # Males are overwhelmed - distribute attention proportionally
                intact_female_success = (intact_female_days_demand / total_female_demand) * breeding_success_ratio
            else:
                # Sufficient males - all intact females get bred
                intact_female_success = 1.0
        else:
            intact_female_success = 0.0

        # Breeding in this 6-month timestep
        litters_per_year = params.get('litters_per_year', 1.4)

        if breeding_season and mature_intact_females > 0 and mature_males > 0:
            # Number of litters per female in this 6-month period
            # Adjusted by male attention availability (reduced if male capacity is insufficient)
            kitten_count = mature_intact_females * (litters_per_year / 2.0) * mean_litter_size * intact_female_success
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

        # Adult mortality: Convert from annual percentage to 6-month rate
        adult_mortality_annual = params.get('adult_mortality_annual', 10) / 100.0  # Convert % to decimal
        timestep_adult_mortality = 1 - ((1 - adult_mortality_annual) ** (1.0/2.0))

        # Apply mortality to adults
        surviving_intact_males = current_intact_males * (1 - timestep_adult_mortality)
        surviving_neutered_males = current_neutered_males * (1 - timestep_adult_mortality)
        surviving_males = surviving_intact_males + surviving_neutered_males
        surviving_intact_females = current_intact_females * (1 - timestep_adult_mortality)
        surviving_treated_females = current_treated_females * (1 - timestep_adult_mortality)

        # Add surviving kittens (split 50/50 male/female)
        # Apply fertility control to new kittens based on settings
        new_female_kittens = surviving_kittens * 0.5
        new_male_kittens = surviving_kittens * 0.5

        if fc_timing == 'one-time' and scenario != 'none' and treatment_pct > 0:
            # One-time: treat proportion of new kittens
            newly_treated = new_female_kittens * (treatment_pct / 100.0)
            newly_neutered = new_male_kittens * (pct_neutered / 100.0)
            new_intact_females = surviving_intact_females + (new_female_kittens - newly_treated)
            new_treated_females = surviving_treated_females + newly_treated
            new_intact_males = surviving_intact_males + (new_male_kittens - newly_neutered)
            new_neutered_males = surviving_neutered_males + newly_neutered
        else:
            # Yearly: no treatment of kittens (treatment happens at yearly intervals)
            new_intact_females = surviving_intact_females + new_female_kittens
            new_treated_females = surviving_treated_females
            new_intact_males = surviving_intact_males + new_male_kittens
            new_neutered_males = surviving_neutered_males

        # Apply arrivals (intact cats arriving from outside - immigration, abandonment)
        # Assume 50:50 sex ratio
        new_arrival_females = arrivals_per_6months / 2.0
        new_arrival_males = arrivals_per_6months / 2.0
        new_intact_females += new_arrival_females
        new_intact_males += new_arrival_males
        total_arrivals += arrivals_per_6months

        # Apply departures (cats leaving - emigration, adoption, shelter removal)
        # Remove proportionally from all groups
        current_total = new_intact_males + new_neutered_males + new_intact_females + new_treated_females
        if current_total > 0 and departures_per_6months > 0:
            departure_rate = min(departures_per_6months / current_total, 1.0)
            departures_this_timestep = min(departures_per_6months, current_total)

            new_intact_males *= (1 - departure_rate)
            new_neutered_males *= (1 - departure_rate)
            new_intact_females *= (1 - departure_rate)
            new_treated_females *= (1 - departure_rate)
            total_departures += departures_this_timestep
        else:
            departures_this_timestep = 0

        # Calculate new population
        new_males = new_intact_males + new_neutered_males
        new_population = new_males + new_intact_females + new_treated_females

        # CRITICAL: Enforce carrying capacity
        # Paper assumes population STAYS at carrying capacity in baseline scenario
        # This is achieved through additional mortality/emigration when over capacity
        if new_population > carrying_capacity:
            # Apply additional density-dependent mortality to bring back to capacity
            excess = new_population - carrying_capacity
            # Remove excess proportionally from all groups
            scale = carrying_capacity / new_population
            new_intact_males *= scale
            new_neutered_males *= scale
            new_males *= scale
            new_intact_females *= scale
            new_treated_females *= scale
            new_population = carrying_capacity

        # Record
        population.append(new_population)
        focal_population_sizes.append(new_population)
        intact_male_count.append(new_intact_males)
        neutered_male_count.append(new_neutered_males)
        male_count.append(new_males)
        intact_female_count.append(new_intact_females)
        treated_female_count.append(new_treated_females)
        pregnant_females_list.append(0)  # Not tracking pregnancies in 6-month model
        estrus_females.append(estrus_count)
        timestep_kittens.append(kitten_count)
        arrivals_list.append(arrivals_per_6months)
        departures_list.append(departures_this_timestep)

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
        'population_sizes': interpolate_to_days(population),
        'females_in_estrus': interpolate_to_days(estrus_females),
        'pregnant_females': interpolate_to_days(pregnant_females_list),
        'males_monopolizing': [0] * len(days),  # Simplified
        'arrivals': interpolate_to_days(arrivals_list),
        'departures': interpolate_to_days(departures_list),
        'total_births': int(total_births),
        'total_deaths': int(total_kitten_deaths),
        'total_kitten_deaths': int(total_kitten_deaths),
        'total_arrivals': int(total_arrivals),
        'total_departures': int(total_departures),
        'kitten_survival_rate': kitten_survival_rate,
    }
