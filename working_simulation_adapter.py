#!/usr/bin/env python3
"""
Simulation engine for the cat population model.

Aggregate (compartmental) model advanced in 6-month timesteps. Breeding adults are
tracked in five buckets:
    intact females, spayed females, AMH-treated females, intact males, neutered males
plus a juvenile queue that imposes a maturation delay so kittens cannot breed until
they reach sexual maturity.

Spayed and AMH females are separate buckets because they behave differently: spayed
females do not cycle (no demand on males), whereas AMH females still cycle and draw
male attention (crowding out intact females) but cannot conceive. Because they are
independent buckets, surgical sterilization and AMH contraception can be applied
together.
"""

import math
import random
from collections import deque

from biological_parameters import (
    ESTRUS_LENGTH_DAYS, ESTROUS_CYCLE_DAYS, MATURE_FRACTION, MATURATION_LAG_TIMESTEPS,
    GESTATION_PERIOD_DAYS, POSTPARTUM_DELAY_DAYS,
    BASE_KITTEN_MORTALITY, HIGH_DENSITY_KITTEN_MORTALITY,
    BREEDING_SEASON_START_MONTH, BREEDING_SEASON_END_MONTH,
    MEAN_LITTER_SIZE, SD_LITTER_SIZE, MIN_LITTER_SIZE, MAX_LITTER_SIZE,
    DEFAULT_LITTERS_PER_YEAR,
    DEFAULT_MALE_BREEDING_CAPACITY_PER_DAY, DEFAULT_AMH_MONOPOLIZATION_DAYS,
    DEFAULT_ADULT_MORTALITY_ANNUAL,
    AMH_BREEDING_DAY_FRACTIONS, DEFAULT_AMH_TREATMENT_AGE,
)

DAYS_IN_TIMESTEP = 182.5  # 6 months


def _survivors(n, p, rng):
    """Number surviving out of n at survival probability p.

    Deterministic mean (n*p) when rng is None; otherwise a normal-approximation
    binomial draw, so variance scales with population size -- demographic
    stochasticity that matters most for small populations.
    """
    if n <= 0:
        return 0.0
    p = min(max(p, 0.0), 1.0)
    if rng is None:
        return n * p
    sd = math.sqrt(n * p * (1 - p))
    return min(max(rng.gauss(n * p, sd), 0.0), n)


def _treatment_count(unit, pct, absolute, available):
    """Number of animals to treat in one intervention event.

    In 'absolute' mode a fixed number is treated (capped at those available); in
    'percentage' mode a fraction of the currently-available intact animals is treated.
    """
    if available <= 0:
        return 0.0
    if unit == 'absolute':
        return min(absolute, available)
    return available * (pct / 100.0)


def run_adapted_simulation(params):
    """Run the cat population simulation and return time series + summary stats."""
    # --- Stochasticity ---
    # rng is None for a deterministic run (default). When 'stochastic' is set, draws
    # are seeded per-run so an ensemble is reproducible.
    rng = random.Random(params.get('_seed', 0)) if params.get('stochastic', False) else None

    # --- Parameters ---
    years = params.get('simulation_years', 10)
    initial_pop = params.get('focal_population', 50)
    pct_spayed = params.get('pct_females_spayed', 0)
    pct_neutered = params.get('pct_males_neutered', 0)
    pct_amh = params.get('pct_females_amh', 0)
    mean_litter_size = params.get('mean_litter_size', MEAN_LITTER_SIZE)

    # Fertility control options
    fc_timing = params.get('fc_timing', 'one-time')   # 'one-time' or 'yearly'
    fc_unit = params.get('fc_unit', 'percentage')     # 'percentage' or 'absolute'
    spay_abs = params.get('fc_females_spayed_absolute', 0)
    amh_abs = params.get('fc_females_amh_absolute', 0)
    neuter_abs = params.get('fc_males_neutered_absolute', 0)

    carrying_capacity = params.get('focal_carrying_capacity', initial_pop)
    use_carrying_capacity = params.get('use_carrying_capacity', True)

    # Running tally of how many animals receive each treatment over the whole run
    total_amh_treated = 0.0
    total_spayed = 0.0
    total_neutered = 0.0

    # --- Initial population split by sex ---
    male_percentage = params.get('male_percentage', 50) / 100.0
    males = initial_pop * male_percentage
    females = initial_pop - males

    # Adult buckets
    intact_females = females
    spayed_females = 0.0
    amh_females = 0.0
    intact_males = males
    neutered_males = 0.0

    # One-time fertility control: applied ONCE to the initial adult population.
    # Spay and AMH may both be applied (spay first, then AMH on the remaining intact
    # females). Recruits that mature or arrive later are NOT re-treated, so coverage
    # decays over time as treated adults die -- this is what "one-time" means.
    if fc_timing == 'one-time':
        n_spay = _treatment_count(fc_unit, pct_spayed, spay_abs, intact_females)
        spayed_females += n_spay; intact_females -= n_spay; total_spayed += n_spay
        n_amh = _treatment_count(fc_unit, pct_amh, amh_abs, intact_females)
        amh_females += n_amh; intact_females -= n_amh; total_amh_treated += n_amh
        n_neuter = _treatment_count(fc_unit, pct_neutered, neuter_abs, intact_males)
        neutered_males += n_neuter; intact_males -= n_neuter; total_neutered += n_neuter

    # --- Juvenile stage (maturation delay) ---
    # Kittens enter a queue and cannot breed until they graduate. Each entry is a
    # [females, males] cohort; the oldest graduates into the intact adult pool after
    # MATURATION_LAG_TIMESTEPS steps.
    maturation_lag = max(1, int(params.get('maturation_lag_timesteps', MATURATION_LAG_TIMESTEPS)))
    juvenile_queue = deque()  # oldest cohort first

    def juvenile_total():
        return sum(f + m for f, m in juvenile_queue)

    # --- Breeding season weighting (see cross-reference in the review notes) ---
    # Cats are seasonally polyestrous (temperate default Jan-Sep). Each 6-month
    # timestep is weighted by how much of its half-year is in season; odd timesteps
    # are the first half of the year (Jan-Jun), even timesteps the second (Jul-Dec).
    # Births are normalized by total_season_frac so realized annual litters equal
    # litters_per_year regardless of season length.
    bs_start = params.get('breeding_season_start_month', BREEDING_SEASON_START_MONTH)
    bs_end = params.get('breeding_season_end_month', BREEDING_SEASON_END_MONTH)
    season_frac_h1 = sum(1 for m in range(1, 7) if bs_start <= m <= bs_end) / 6.0
    season_frac_h2 = sum(1 for m in range(7, 13) if bs_start <= m <= bs_end) / 6.0
    total_season_frac = season_frac_h1 + season_frac_h2

    # --- Physiological ceiling on litters per year (how gestation & postpartum enter) ---
    # A queen must carry a litter to term (gestation) then recover (postpartum) and
    # return to a fertile estrus before the next litter, so the minimum interval is
    # gestation + postpartum + ~half an estrous cycle. litters_per_year cannot exceed
    # what this interval physically allows.
    reproductive_interval_days = (GESTATION_PERIOD_DAYS + POSTPARTUM_DELAY_DAYS
                                  + ESTROUS_CYCLE_DAYS / 2.0)
    max_litters_per_year = 365.0 / reproductive_interval_days
    requested_litters_per_year = params.get('litters_per_year', DEFAULT_LITTERS_PER_YEAR)
    effective_litters_per_year = min(requested_litters_per_year, max_litters_per_year)

    # --- Other fixed / adjustable parameters ---
    male_cap_per_day = params.get('male_breeding_capacity_per_day', DEFAULT_MALE_BREEDING_CAPACITY_PER_DAY)
    estrus_ratio_intact = ESTRUS_LENGTH_DAYS / ESTROUS_CYCLE_DAYS  # used only for the estrus display
    # Male-attention demand uses empirically-observed breeding-day fractions (the share
    # of days each female type is actually seen mating). Intact females mate on few days
    # because they are pregnant/postpartum much of the time; AMH females never conceive
    # so they stay available and mate on more days. The fractions depend on age at AMH
    # treatment (kitten vs adult).
    amh_treatment_age = params.get('amh_treatment_age', DEFAULT_AMH_TREATMENT_AGE)
    _bd = AMH_BREEDING_DAY_FRACTIONS.get(amh_treatment_age, AMH_BREEDING_DAY_FRACTIONS['adult'])
    intact_breeding_fraction = _bd['intact']
    amh_breeding_fraction = _bd['amh']
    base_kitten_mortality = params.get('base_kitten_mortality', BASE_KITTEN_MORTALITY)
    high_density_mortality = params.get('high_density_mortality', HIGH_DENSITY_KITTEN_MORTALITY)
    annual_adult_mortality = params.get('adult_mortality_annual', DEFAULT_ADULT_MORTALITY_ANNUAL) / 100.0
    timestep_adult_survival = (1 - annual_adult_mortality) ** 0.5  # per 6 months

    arrivals_per_year = params.get('arrivals_per_year', 10)
    departures_per_year = params.get('departures_per_year', 10)
    arrivals_per_6months = arrivals_per_year / 2.0
    departures_per_6months = departures_per_year / 2.0

    # --- Time series ---
    timesteps = years * 2
    population = [initial_pop]
    estrus_series = [0.0]
    arrivals_series = [0.0]
    departures_series = [0.0]

    total_births = 0.0
    total_kitten_deaths = 0.0
    total_arrivals = 0.0
    total_departures = 0.0

    for timestep in range(1, timesteps + 1):
        season_frac = season_frac_h1 if (timestep % 2 == 1) else season_frac_h2
        breeding_season = season_frac > 0

        # --- Yearly fertility control: treat current intact adults each year ---
        if fc_timing == 'yearly' and timestep % 2 == 0:  # every 2 timesteps = 1 year
            n_spay = _treatment_count(fc_unit, pct_spayed, spay_abs, intact_females)
            spayed_females += n_spay; intact_females -= n_spay; total_spayed += n_spay
            n_amh = _treatment_count(fc_unit, pct_amh, amh_abs, intact_females)
            amh_females += n_amh; intact_females -= n_amh; total_amh_treated += n_amh
            n_neuter = _treatment_count(fc_unit, pct_neutered, neuter_abs, intact_males)
            neutered_males += n_neuter; intact_males -= n_neuter; total_neutered += n_neuter

        # --- Density (uses total population incl. juveniles) ---
        current_pop = (intact_females + spayed_females + amh_females
                       + intact_males + neutered_males + juvenile_total())
        density = (current_pop / carrying_capacity) if use_carrying_capacity else 0.0

        # --- Mature breeders ---
        mature_intact_females = intact_females * MATURE_FRACTION
        mature_amh_females = amh_females * MATURE_FRACTION
        mature_intact_males = intact_males * MATURE_FRACTION

        # --- Male attention supply/demand (female-days over the in-season period) ---
        season_days = DAYS_IN_TIMESTEP * season_frac
        male_capacity = mature_intact_males * male_cap_per_day * season_days
        intact_demand = mature_intact_females * intact_breeding_fraction * season_days
        amh_demand = mature_amh_females * amh_breeding_fraction * season_days  # AMH stays available -> crowds out
        total_demand = intact_demand + amh_demand
        # Male attention is shared proportionally across all demand, so the fraction of
        # intact females that conceive equals the overall fill rate. AMH females inflate
        # total_demand and therefore lower that rate -- the crowding-out benefit of AMH.
        if total_demand > 0 and male_capacity > 0:
            intact_female_success = min(1.0, male_capacity / total_demand)
        else:
            intact_female_success = 0.0

        estrus_count = mature_intact_females * estrus_ratio_intact if breeding_season else 0.0

        # --- Births ---
        if breeding_season and mature_intact_females > 0 and mature_intact_males > 0:
            # Litters allocated to this timestep in proportion to its in-season fraction,
            # normalized so the annual total equals effective_litters_per_year.
            litter_share = (season_frac / total_season_frac) if total_season_frac > 0 else 0.0
            # Litter size varies between years (environmental stochasticity) when enabled.
            if rng is not None:
                litter_size = min(max(rng.gauss(mean_litter_size, SD_LITTER_SIZE),
                                      MIN_LITTER_SIZE), MAX_LITTER_SIZE)
            else:
                litter_size = mean_litter_size
            kitten_count = (mature_intact_females * effective_litters_per_year * litter_share
                            * litter_size * intact_female_success)
            # Demographic birth noise (Poisson-like: variance ~ mean).
            if rng is not None and kitten_count > 0:
                kitten_count = max(0.0, rng.gauss(kitten_count, math.sqrt(kitten_count)))
        else:
            kitten_count = 0.0
        total_births += kitten_count

        # --- Density-dependent kitten mortality ---
        if density < 1.0:
            kitten_mortality = base_kitten_mortality + density * (high_density_mortality - base_kitten_mortality)
        else:
            kitten_mortality = high_density_mortality
        surviving_kittens = _survivors(kitten_count, 1 - kitten_mortality, rng)
        kitten_deaths = kitten_count - surviving_kittens
        total_kitten_deaths += kitten_deaths

        # --- Adult mortality (applied to adults and to maturing juveniles) ---
        intact_females = _survivors(intact_females, timestep_adult_survival, rng)
        spayed_females = _survivors(spayed_females, timestep_adult_survival, rng)
        amh_females = _survivors(amh_females, timestep_adult_survival, rng)
        intact_males = _survivors(intact_males, timestep_adult_survival, rng)
        neutered_males = _survivors(neutered_males, timestep_adult_survival, rng)
        for cohort in juvenile_queue:
            cohort[0] = _survivors(cohort[0], timestep_adult_survival, rng)
            cohort[1] = _survivors(cohort[1], timestep_adult_survival, rng)

        # --- Graduate matured juveniles into the intact adult pool ---
        if len(juvenile_queue) >= maturation_lag:
            grad_f, grad_m = juvenile_queue.popleft()
            intact_females += grad_f
            intact_males += grad_m

        # --- This timestep's surviving kittens become the youngest juvenile cohort ---
        juvenile_queue.append([surviving_kittens * 0.5, surviving_kittens * 0.5])

        # --- Arrivals (intact adults, 50:50 sex) ---
        intact_females += arrivals_per_6months / 2.0
        intact_males += arrivals_per_6months / 2.0
        total_arrivals += arrivals_per_6months

        # --- Departures (proportional across all adults and juveniles) ---
        adult_total = intact_females + spayed_females + amh_females + intact_males + neutered_males
        current_total = adult_total + juvenile_total()
        if current_total > 0 and departures_per_6months > 0:
            dep_rate = min(departures_per_6months / current_total, 1.0)
            departures_ts = min(departures_per_6months, current_total)
            keep = 1 - dep_rate
            intact_females *= keep; spayed_females *= keep; amh_females *= keep
            intact_males *= keep; neutered_males *= keep
            for cohort in juvenile_queue:
                cohort[0] *= keep; cohort[1] *= keep
            total_departures += departures_ts
        else:
            departures_ts = 0.0

        # --- Enforce carrying capacity (hard proportional ceiling) ---
        new_population = (intact_females + spayed_females + amh_females
                          + intact_males + neutered_males + juvenile_total())
        if use_carrying_capacity and new_population > carrying_capacity:
            scale = carrying_capacity / new_population
            intact_females *= scale; spayed_females *= scale; amh_females *= scale
            intact_males *= scale; neutered_males *= scale
            for cohort in juvenile_queue:
                cohort[0] *= scale; cohort[1] *= scale
            new_population = carrying_capacity

        population.append(new_population)
        estrus_series.append(estrus_count)
        arrivals_series.append(arrivals_per_6months)
        departures_series.append(departures_ts)

    # --- Resample the 6-month series to ~monthly points for smooth plots ---
    simulation_days = years * 365
    sample_interval = 30
    days = list(range(0, simulation_days, sample_interval))

    def interpolate_to_days(timestep_data):
        """Linearly interpolate between 6-month timesteps for smooth visualization."""
        daily_data = []
        for day in days:
            timestep_float = day / DAYS_IN_TIMESTEP
            timestep_idx = int(timestep_float)
            if timestep_idx >= len(timestep_data) - 1:
                daily_data.append(timestep_data[-1])
            else:
                fraction = timestep_float - timestep_idx
                start = timestep_data[timestep_idx]
                end = timestep_data[timestep_idx + 1]
                daily_data.append(start + (end - start) * fraction)
        return daily_data

    kittens_survived = total_births - total_kitten_deaths
    kitten_survival_rate = kittens_survived / total_births if total_births > 0 else 0

    return {
        'days': days,
        'focal_population_sizes': interpolate_to_days(population),
        'population_sizes': interpolate_to_days(population),
        'females_in_estrus': interpolate_to_days(estrus_series),
        'pregnant_females': [0] * len(days),           # not tracked in the 6-month model
        'males_monopolizing': [0] * len(days),          # simplified
        'arrivals': interpolate_to_days(arrivals_series),
        'departures': interpolate_to_days(departures_series),
        'total_births': int(total_births),
        'total_deaths': int(total_kitten_deaths),
        'total_kitten_deaths': int(total_kitten_deaths),
        'total_arrivals': int(total_arrivals),
        'total_departures': int(total_departures),
        'kitten_survival_rate': kitten_survival_rate,
        'total_amh_treated': int(round(total_amh_treated)),
        'total_spayed': int(round(total_spayed)),
        'total_neutered': int(round(total_neutered)),
        'max_litters_per_year': round(max_litters_per_year, 2),
        'effective_litters_per_year': round(effective_litters_per_year, 2),
    }


def _percentile(values, q):
    """Linear-interpolated percentile of a list (q in [0, 1])."""
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * q
    f = int(k)
    if f + 1 >= len(s):
        return s[-1]
    return s[f] + (s[f + 1] - s[f]) * (k - f)


def run_simulation_ensemble(params, n_simulations):
    """Run n stochastic trajectories and aggregate them.

    Returns the same shape as a single run (so the UI/plots work unchanged), with the
    population line = mean across runs, plus a 5th-95th percentile band, final-population
    mean and interval, and the probability of near-eradication (final population < 1).
    """
    n = max(1, int(n_simulations))
    runs = [run_adapted_simulation({**params, 'stochastic': True, '_seed': seed})
            for seed in range(n)]
    days = runs[0]['days']
    pop_matrix = [r['population_sizes'] for r in runs]

    mean_series, lower, upper = [], [], []
    for t in range(len(days)):
        col = [run[t] for run in pop_matrix]
        mean_series.append(sum(col) / n)
        lower.append(_percentile(col, 0.05))
        upper.append(_percentile(col, 0.95))

    finals = [r['population_sizes'][-1] for r in runs]

    def avg(key):
        return sum(r[key] for r in runs) / n

    base = runs[0]
    return {
        'days': days,
        'population_sizes': mean_series,
        'focal_population_sizes': mean_series,
        'population_sizes_lower': lower,
        'population_sizes_upper': upper,
        'females_in_estrus': base['females_in_estrus'],
        'pregnant_females': base['pregnant_females'],
        'males_monopolizing': base['males_monopolizing'],
        'arrivals': base['arrivals'],
        'departures': base['departures'],
        'total_births': int(avg('total_births')),
        'total_deaths': int(avg('total_deaths')),
        'total_kitten_deaths': int(avg('total_kitten_deaths')),
        'total_arrivals': int(avg('total_arrivals')),
        'total_departures': int(avg('total_departures')),
        'kitten_survival_rate': avg('kitten_survival_rate'),
        'total_amh_treated': int(round(avg('total_amh_treated'))),
        'total_spayed': int(round(avg('total_spayed'))),
        'total_neutered': int(round(avg('total_neutered'))),
        'max_litters_per_year': base['max_litters_per_year'],
        'effective_litters_per_year': base['effective_litters_per_year'],
        'n_simulations': n,
        'final_population_mean': round(sum(finals) / n, 1),
        'final_population_lower': round(_percentile(finals, 0.05), 1),
        'final_population_upper': round(_percentile(finals, 0.95), 1),
        'prob_near_eradication': round(sum(1 for f in finals if f < 1.0) / n, 3),
    }
