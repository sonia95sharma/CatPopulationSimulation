#!/usr/bin/env python3
"""
Behavioral tests for the cat population simulation engine.

Plain-assert tests (no external test framework needed). Run with:
    python test_simulation.py

Each test checks a modeled behavior rather than an exact number, so the suite
stays meaningful if constants are re-calibrated.
"""

from working_simulation_adapter import run_adapted_simulation, run_simulation_ensemble


def base(**kw):
    """A default parameter set; override individual keys via kwargs."""
    p = dict(
        simulation_years=10, focal_population=100, male_percentage=50,
        litters_per_year=2.0, mean_litter_size=4.0, adult_mortality_annual=10,
        arrivals_per_year=0, departures_per_year=0,
        base_kitten_mortality=0.90, high_density_mortality=0.95,
        male_breeding_capacity_per_day=3.0,
        pct_females_amh=0, pct_females_spayed=0, pct_males_neutered=0,
        fc_unit='percentage', fc_timing='one-time',
        use_carrying_capacity=True, focal_carrying_capacity=200,
        cost_amh_per_female=100, cost_spay_per_female=80, cost_neuter_per_male=40,
    )
    p.update(kw)
    return p


def final_pop(r):
    return r['population_sizes'][-1]


def test_deterministic_is_reproducible():
    a = run_adapted_simulation(base())
    b = run_adapted_simulation(base())
    assert a['population_sizes'] == b['population_sizes'], "deterministic run should be identical each time"


def test_carrying_capacity_is_a_ceiling():
    r = run_adapted_simulation(base(focal_carrying_capacity=200))
    assert final_pop(r) <= 200 + 1e-6, "population must not exceed carrying capacity"


def test_infinite_growth_when_capacity_disabled():
    capped = run_adapted_simulation(base(focal_carrying_capacity=200, use_carrying_capacity=True))
    uncapped = run_adapted_simulation(base(focal_carrying_capacity=200, use_carrying_capacity=False))
    assert final_pop(uncapped) > final_pop(capped), "disabling carrying capacity should allow more growth"


def test_no_treatment_is_counted_when_none_applied():
    r = run_adapted_simulation(base())
    assert r['total_spayed'] == 0 and r['total_amh_treated'] == 0 and r['total_neutered'] == 0
    assert r['total_cost'] == 0, "no treatment should cost nothing"


def test_treatment_is_counted():
    r = run_adapted_simulation(base(pct_females_spayed=50))
    assert r['total_spayed'] > 0, "spaying should record the number of animals treated"


def test_cost_tracks_treatment():
    r = run_adapted_simulation(base(pct_females_spayed=50))
    assert r['cost_spay_total'] > 0 and r['total_cost'] > 0
    total = r['cost_amh_total'] + r['cost_spay_total'] + r['cost_neuter_total']
    assert abs(r['total_cost'] - total) < 0.01, "total cost should be the sum of the components"


def test_spay_and_amh_combine():
    r = run_adapted_simulation(base(pct_females_spayed=30, pct_females_amh=30, pct_males_neutered=10))
    assert r['total_spayed'] > 0 and r['total_amh_treated'] > 0 and r['total_neutered'] > 0, \
        "spay, AMH and neuter should all apply together"


def test_yearly_suppresses_more_than_one_time():
    one_time = run_adapted_simulation(base(pct_females_spayed=50, fc_timing='one-time',
                                           focal_carrying_capacity=10**9, use_carrying_capacity=False))
    yearly = run_adapted_simulation(base(pct_females_spayed=50, fc_timing='yearly',
                                         focal_carrying_capacity=10**9, use_carrying_capacity=False))
    assert yearly['total_spayed'] > one_time['total_spayed'], "yearly should treat more animals over time"
    assert final_pop(yearly) < final_pop(one_time), "yearly should suppress the population more"


def test_reproductive_ceiling_caps_litters():
    r = run_adapted_simulation(base(litters_per_year=3.0))
    assert r['effective_litters_per_year'] <= r['max_litters_per_year'] + 1e-9
    assert r['effective_litters_per_year'] < 3.0, "3.0 litters/year should be trimmed to the physiological max"


def test_maturation_delay_curbs_growth():
    # With a ~12-month maturation delay, unmanaged uncapped growth should be well below
    # the runaway rate a no-delay model produced (~86%/yr); expect a sane double-digit rate.
    r = run_adapted_simulation(base(focal_population=50, focal_carrying_capacity=10**9,
                                    use_carrying_capacity=False))
    annual_growth = (final_pop(r) / 50) ** (1 / 10) - 1
    assert 0.0 < annual_growth < 0.75, f"growth rate {annual_growth:.2f} outside the plausible range"


def test_amh_crowding_only_when_males_scarce():
    # Normal sex ratio: AMH and spay should be essentially identical (no crowding).
    spay = run_adapted_simulation(base(pct_females_spayed=60, fc_timing='yearly'))
    amh = run_adapted_simulation(base(pct_females_amh=60, fc_timing='yearly'))
    assert abs(final_pop(spay) - final_pop(amh)) < 1.0, "AMH and spay should match when males are not limiting"

    # Scarce males: AMH should suppress at least as much as spay (crowding).
    scarce = dict(male_percentage=8, male_breeding_capacity_per_day=1.0,
                  focal_carrying_capacity=10**9, use_carrying_capacity=False, fc_timing='yearly')
    spay_s = run_adapted_simulation(base(pct_females_spayed=50, **scarce))
    amh_s = run_adapted_simulation(base(pct_females_amh=50, **scarce))
    assert final_pop(amh_s) <= final_pop(spay_s) + 1e-6, "AMH should not do worse than spay when males are scarce"


def test_stochastic_ensemble_shape():
    r = run_simulation_ensemble(base(pct_females_spayed=40, fc_timing='yearly'), 50)
    assert r['n_simulations'] == 50
    lo, mid, hi = r['population_sizes_lower'][-1], r['population_sizes'][-1], r['population_sizes_upper'][-1]
    assert lo <= mid <= hi, "confidence band must bracket the mean"
    assert 0.0 <= r['prob_near_eradication'] <= 1.0


def test_ensemble_is_reproducible():
    a = run_simulation_ensemble(base(pct_females_amh=30, fc_timing='yearly'), 30)
    b = run_simulation_ensemble(base(pct_females_amh=30, fc_timing='yearly'), 30)
    assert a['final_population_mean'] == b['final_population_mean'], "seeded ensemble should be reproducible"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    passed = 0
    for t in tests:
        t()
        print(f"  PASS  {t.__name__}")
        passed += 1
    print(f"\n{passed}/{len(tests)} tests passed")


if __name__ == '__main__':
    main()
