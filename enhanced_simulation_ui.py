#!/usr/bin/env python3
"""
Enhanced Population Simulation UI with Detailed Biological Parameters
Includes estrous cycles, male monopolization, AMH contraception, and more
"""

import os
import tempfile
# matplotlib needs a writable config/cache dir. On serverless hosts (e.g. Vercel)
# only the temp dir is writable, so point it there before importing matplotlib.
os.environ.setdefault('MPLCONFIGDIR', os.path.join(tempfile.gettempdir(), 'matplotlib'))

from flask import Flask, render_template, request, jsonify, send_file
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from biological_parameters import (
    ESTROUS_CYCLE_DAYS, ESTRUS_LENGTH_DAYS,
    FEMALE_MATURITY_MEAN_MONTHS, FEMALE_MATURITY_SD_MONTHS,
    FEMALE_MATURITY_MIN_MONTHS, FEMALE_MATURITY_MAX_MONTHS,
    MALE_MATURITY_MEAN_MONTHS, MALE_MATURITY_MIN_MONTHS, MALE_MATURITY_MAX_MONTHS,
    GESTATION_PERIOD_DAYS, POSTPARTUM_DELAY_DAYS,
    MEAN_LITTER_SIZE, SD_LITTER_SIZE, MIN_LITTER_SIZE, MAX_LITTER_SIZE,
    BASE_KITTEN_MORTALITY, HIGH_DENSITY_KITTEN_MORTALITY,
    BREEDING_SEASON_START_MONTH, BREEDING_SEASON_END_MONTH,
    MATURE_FRACTION, MATURATION_LAG_TIMESTEPS,
    AMH_BREEDING_DAY_FRACTIONS,
)
from datetime import datetime
import csv

app = Flask(__name__)

# Store simulation runs for comparison
simulation_history = []

@app.route('/')
def index():
    """Render the main UI page with all biological parameter controls"""
    return render_template('enhanced_index.html')


@app.route('/assumptions')
def assumptions():
    """Page listing every fixed / assumed value the model uses, with sources.

    Values are pulled from biological_parameters.py (the single source of truth) so
    this page always reflects what the engine actually uses; the citations are the
    peer-reviewed sources those values are drawn from or calibrated against.
    """
    non_estrus = ESTROUS_CYCLE_DAYS - ESTRUS_LENGTH_DAYS
    repro_interval = GESTATION_PERIOD_DAYS + POSTPARTUM_DELAY_DAYS + ESTROUS_CYCLE_DAYS / 2.0
    max_litters = round(365.0 / repro_interval, 2)
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December']

    sections = [
        {
            'title': 'Reproductive cycle',
            'rows': [
                {'param': 'Estrous cycle length',
                 'value': f'{ESTROUS_CYCLE_DAYS} days ({ESTRUS_LENGTH_DAYS}-day estrus + {non_estrus}-day interval)',
                 'source': 'Shille, Lundström & Stabenfeldt (1979). Estrus 7.4 d (SD 3.7; range 2–19); '
                           'inter-estrus interval 9.0 d (SD 7.6; range 4–22); rounded for whole-day arithmetic.'},
                {'param': 'Gestation period',
                 'value': f'{GESTATION_PERIOD_DAYS} days',
                 'source': 'Ng, Fascetti & Larsen (2023), review of multiple sources.'},
                {'param': 'Postpartum delay before re-conception',
                 'value': f'{POSTPARTUM_DELAY_DAYS} days (8 weeks)',
                 'source': 'Wildt et al. (1981); Griffin (2001).'},
                {'param': 'Reproductive interval (derived)',
                 'value': f'{int(repro_interval)} days → max {max_litters} litters/year',
                 'source': 'Derived: gestation + postpartum + ~½ estrous cycle. Caps the requested '
                           'litters/year to what is physiologically possible.'},
            ],
        },
        {
            'title': 'Age at sexual maturity',
            'rows': [
                {'param': 'Females',
                 'value': f'{FEMALE_MATURITY_MEAN_MONTHS:g} months (SD {FEMALE_MATURITY_SD_MONTHS:g}; '
                          f'range {int(FEMALE_MATURITY_MIN_MONTHS)}–{int(FEMALE_MATURITY_MAX_MONTHS)})',
                 'source': 'Jemmett & Evans (1977); Festing & Bleby (1970), via Ng et al. (2023).'},
                {'param': 'Males',
                 'value': f'{MALE_MATURITY_MEAN_MONTHS:g} months '
                          f'(range {int(MALE_MATURITY_MIN_MONTHS)}–{int(MALE_MATURITY_MAX_MONTHS)})',
                 'source': 'Johnson (2022); Kutzler (2022); Pintus et al. (2021).'},
                {'param': 'Maturation delay in model',
                 'value': f'{MATURATION_LAG_TIMESTEPS} timestep (~12 months to first breeding)',
                 'source': 'Derived from the maturity ages plus the seasonal reality that kittens born '
                           'in one breeding season generally do not breed until the next.'},
            ],
        },
        {
            'title': 'Litters',
            'rows': [
                {'param': 'Mean litter size',
                 'value': f'{MEAN_LITTER_SIZE:g} kittens (SD {SD_LITTER_SIZE:g}; '
                          f'range {MIN_LITTER_SIZE}–{MAX_LITTER_SIZE})',
                 'source': 'Fournier et al. (2017); Robinson & Cox (1970).'},
            ],
        },
        {
            'title': 'Mortality',
            'rows': [
                {'param': 'Kitten mortality (low density)',
                 'value': f'{int(BASE_KITTEN_MORTALITY * 100)}%',
                 'source': 'Density-dependent; calibrated so unmanaged growth matches Miller et al. (2014) '
                           '(~18–20%/yr) and sterilization response matches Boone et al. (2019).'},
                {'param': 'Kitten mortality (at carrying capacity)',
                 'value': f'{int(HIGH_DENSITY_KITTEN_MORTALITY * 100)}%',
                 'source': 'Interpolated linearly from the low-density rate as the population approaches '
                           'carrying capacity. Within the high mortality reported for free-roaming kittens.'},
            ],
        },
        {
            'title': 'Breeding season & population',
            'rows': [
                {'param': 'Breeding season',
                 'value': f'{months[BREEDING_SEASON_START_MONTH-1]}–{months[BREEDING_SEASON_END_MONTH-1]}',
                 'source': 'Cats are seasonally polyestrous in temperate climates. Realized annual litters '
                           'are held to the litters/year setting regardless of season length.'},
                {'param': 'Fraction of adults sexually mature',
                 'value': f'{int(MATURE_FRACTION * 100)}%',
                 'source': 'Aggregate model proxy for the mature share of each adult group.'},
            ],
        },
        {
            'title': 'AMH contraception behavior (male-attention model)',
            'rows': [
                {'param': 'Breeding-day fraction — treated as adults',
                 'value': f"intact {int(AMH_BREEDING_DAY_FRACTIONS['adult']['intact']*100)}% of days / "
                          f"AMH {int(AMH_BREEDING_DAY_FRACTIONS['adult']['amh']*100)}% of days",
                 'source': 'Controlled AMH gene-therapy mating trials (adult treatment). Treated females never '
                           'conceive, so they stay available to mate more than intact females, which are pregnant '
                           'or recovering most of the year.'},
                {'param': 'Breeding-day fraction — treated as kittens',
                 'value': f"intact {int(AMH_BREEDING_DAY_FRACTIONS['kitten']['intact']*100)}% of days / "
                          f"AMH {int(AMH_BREEDING_DAY_FRACTIONS['kitten']['amh']*100)}% of days",
                 'source': 'Prepubertal AMH gene-therapy trial (treated bred ~34–47% of days vs ~15% for controls).'},
                {'param': 'AMH contraceptive efficacy',
                 'value': '100% (modeled)',
                 'source': 'Adult and prepubertal trials both reported zero pregnancies in treated females (small '
                           'samples). Modeled as fully effective and permanent, though durability is demonstrated '
                           'only to ~3 years.'},
            ],
        },
    ]

    modeling_notes = [
        'The model can run as a single deterministic trajectory, or as a stochastic ensemble (multiple runs) '
        'that shows a mean, a 90% confidence band, and the probability of near-eradication.',
        'Time advances in 6-month timesteps.',
        'Adult mortality is applied at a constant annual rate (adjustable), independent of density.',
        'Kitten survival is the main density-dependent regulator of population size.',
        'Arrivals and departures assume a 50:50 sex ratio.',
        'The AMH "crowding" advantage over spaying is a hypothesis, not an established population-level effect; '
        'in the model it appears only when intact males are a scarce, limiting resource.',
    ]

    return render_template('assumptions.html', sections=sections, modeling_notes=modeling_notes)


@app.route('/how-it-works')
def how_it_works():
    """Plain-language explanation of the simulation's mechanics.

    Numeric values are pulled from biological_parameters.py so the explanation stays
    consistent with what the engine actually uses.
    """
    repro_interval = GESTATION_PERIOD_DAYS + POSTPARTUM_DELAY_DAYS + ESTROUS_CYCLE_DAYS / 2.0
    v = {
        'estrus_days': ESTRUS_LENGTH_DAYS,
        'cycle_days': ESTROUS_CYCLE_DAYS,
        'non_estrus_days': ESTROUS_CYCLE_DAYS - ESTRUS_LENGTH_DAYS,
        'gestation': GESTATION_PERIOD_DAYS,
        'postpartum': POSTPARTUM_DELAY_DAYS,
        'max_litters': round(365.0 / repro_interval, 2),
        'base_kmort': int(round(BASE_KITTEN_MORTALITY * 100)),
        'high_kmort': int(round(HIGH_DENSITY_KITTEN_MORTALITY * 100)),
        'mature_pct': int(round(MATURE_FRACTION * 100)),
        'mean_litter': f'{MEAN_LITTER_SIZE:g}',
        'female_maturity': f'{FEMALE_MATURITY_MEAN_MONTHS:g}',
        'male_maturity': f'{MALE_MATURITY_MEAN_MONTHS:g}',
    }
    return render_template('how_it_works.html', v=v)


@app.route('/run_enhanced_simulation', methods=['POST'])
def run_enhanced_simulation():
    """Run simulation with detailed biological parameters"""
    try:
        data = request.json

        # Fixed biological parameters. Single source of truth: biological_parameters.py
        # (these are not adjustable via the UI, to keep the biology consistent).
        estrous_cycle_length = ESTROUS_CYCLE_DAYS
        estrus_length = ESTRUS_LENGTH_DAYS

        female_maturity_mean_months = FEMALE_MATURITY_MEAN_MONTHS
        female_maturity_sd_months = FEMALE_MATURITY_SD_MONTHS
        female_maturity_min_months = FEMALE_MATURITY_MIN_MONTHS
        female_maturity_max_months = FEMALE_MATURITY_MAX_MONTHS

        male_maturity_mean_months = MALE_MATURITY_MEAN_MONTHS
        male_maturity_min_months = MALE_MATURITY_MIN_MONTHS
        male_maturity_max_months = MALE_MATURITY_MAX_MONTHS

        gestation_period_days = GESTATION_PERIOD_DAYS
        postpartum_delay_days = POSTPARTUM_DELAY_DAYS

        mean_litter_size = MEAN_LITTER_SIZE
        sd_litter_size = SD_LITTER_SIZE
        min_litter_size = MIN_LITTER_SIZE
        max_litter_size = MAX_LITTER_SIZE

        # Extract fertility control options
        fc_unit = data.get('fc_unit', 'percentage')  # 'percentage' or 'absolute'
        fc_timing = data.get('fc_timing', 'one-time')  # 'one-time' or 'yearly'

        # Get fertility control values
        fc_females_amh = float(data.get('pct_females_amh', 0))
        fc_females_spayed = float(data.get('pct_females_spayed', 0))
        fc_males_neutered = float(data.get('pct_males_neutered', 0))

        # Convert to percentages if needed
        focal_pop = int(data.get('focal_population', 50))
        if fc_unit == 'absolute':
            # Convert absolute numbers to percentages for initial calculation
            pct_females_amh = (fc_females_amh / focal_pop * 100) if focal_pop > 0 else 0
            pct_females_spayed = (fc_females_spayed / focal_pop * 100) if focal_pop > 0 else 0
            pct_males_neutered = (fc_males_neutered / focal_pop * 100) if focal_pop > 0 else 0
        else:
            pct_females_amh = fc_females_amh
            pct_females_spayed = fc_females_spayed
            pct_males_neutered = fc_males_neutered

        # Extract adjustable parameters from UI
        params = {
            # HARDCODED biological parameters
            'estrous_cycle_length': estrous_cycle_length,
            'estrus_length': estrus_length,
            'female_maturity_min_months': female_maturity_min_months,
            'female_maturity_max_months': female_maturity_max_months,
            'female_maturity_mean_months': female_maturity_mean_months,
            'female_maturity_sd_months': female_maturity_sd_months,
            'male_maturity_months': male_maturity_mean_months,
            'male_maturity_min_months': male_maturity_min_months,
            'male_maturity_max_months': male_maturity_max_months,
            'gestation_period_days': gestation_period_days,
            'postpartum_delay_days': postpartum_delay_days,
            'mean_litter_size': mean_litter_size,
            'sd_litter_size': sd_litter_size,
            'max_litter_size': max_litter_size,
            'min_litter_size': min_litter_size,

            # Breeding season (temperate Jan-Sep; cats are seasonally polyestrous)
            'breeding_season_start_month': BREEDING_SEASON_START_MONTH,
            'breeding_season_end_month': BREEDING_SEASON_END_MONTH,

            # Male breeding capacity (still adjustable)
            'male_breeding_capacity_per_day': float(data.get('male_breeding_capacity_per_day', 3.0)),
            # Age at AMH treatment sets the breeding-day fractions used for crowding
            'amh_treatment_age': data.get('amh_treatment_age', 'adult'),

            # Breeding parameters (still adjustable)
            'litters_per_year': float(data.get('litters_per_year', 2.0)),

            # Fertility control (converted to percentages)
            'pct_females_amh': pct_females_amh,
            'pct_females_spayed': pct_females_spayed,
            'pct_males_neutered': pct_males_neutered,

            # Fertility control options
            'fc_unit': fc_unit,
            'fc_timing': fc_timing,
            'fc_females_amh_absolute': fc_females_amh if fc_unit == 'absolute' else 0,
            'fc_females_spayed_absolute': fc_females_spayed if fc_unit == 'absolute' else 0,
            'fc_males_neutered_absolute': fc_males_neutered if fc_unit == 'absolute' else 0,

            # Simulation settings (still adjustable)
            'simulation_years': int(data.get('simulation_years', 10)),
            'simulation_days': int(data.get('simulation_years', 10)) * 365,
            'n_simulations': int(data.get('n_simulations', 1)),

            # Focal population (still adjustable)
            'focal_population': int(data.get('focal_population', 50)),
            'male_percentage': float(data.get('male_percentage', 50)),
            'focal_carrying_capacity': int(data.get('focal_carrying_capacity', 200)),

            # Population dynamics (still adjustable)
            'arrivals_per_year': int(data.get('arrivals_per_year', 10)),
            'departures_per_year': int(data.get('departures_per_year', 10)),

            # Mortality parameters
            'adult_mortality_annual': float(data.get('adult_mortality_annual', 10)),
            # Kitten mortality (density-dependent; single source of truth)
            'base_kitten_mortality': BASE_KITTEN_MORTALITY,
            'high_density_mortality': HIGH_DENSITY_KITTEN_MORTALITY,

            # Carrying capacity toggle (False = infinite growth, no maximum population)
            'use_carrying_capacity': bool(data.get('use_carrying_capacity', True)),


            # Legacy support
            'initial_adult_population': int(data.get('initial_adult_population',
                                                    data.get('focal_population', 50))),
            'initial_female_percentage': float(data.get('initial_female_percentage', 50)),
            'carrying_capacity': int(data.get('carrying_capacity',
                                             data.get('focal_carrying_capacity', 200))),
        }

        # Run working simulation via adapter (ensemble of stochastic runs if requested)
        from working_simulation_adapter import run_adapted_simulation, run_simulation_ensemble
        n_sims = params['n_simulations']
        if n_sims > 1:
            results = run_simulation_ensemble(params, n_sims)
        else:
            results = run_adapted_simulation(params)

        # Generate plots
        plot_data = generate_enhanced_plots(results)

        # Prepare response with run metadata
        response = {
            'success': True,
            'results': results,
            'plots': plot_data,
            'parameters_used': params,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response)

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def generate_enhanced_plots(results):
    """Generate population plot"""

    fig, ax = plt.subplots(figsize=(12, 6))

    days_in_years = [d / 365 for d in results['days']]

    # Confidence band for stochastic ensembles (5th-95th percentile across runs)
    if results.get('population_sizes_lower') and results.get('population_sizes_upper'):
        ax.fill_between(days_in_years, results['population_sizes_lower'],
                        results['population_sizes_upper'], color='#1e3a5f', alpha=0.18,
                        label=f"90% interval ({results.get('n_simulations', 0)} runs)")

    # Plot focal population
    if 'focal_population_sizes' in results:
        line_label = 'Mean population' if results.get('n_simulations', 1) > 1 else 'Focal Population'
        ax.plot(days_in_years, results['focal_population_sizes'], color='#1e3a5f', linewidth=3,
                label=line_label, marker='o', markersize=4)
        ax.set_title('Population Dynamics Over Time', fontsize=18, fontweight='bold', pad=20)
    else:
        ax.plot(days_in_years, results['population_sizes'], color='#1e3a5f', linewidth=3, marker='o', markersize=4)
        ax.set_title('Population Over Time', fontsize=18, fontweight='bold', pad=20)

    ax.set_xlabel('Years', fontsize=14, fontweight='bold')
    ax.set_ylabel('Population Size', fontsize=14, fontweight='bold')
    ax.legend(fontsize=12, loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle='--')

    # Add summary text below the plot
    if 'focal_population_sizes' in results:
        initial_pop = int(round(results['focal_population_sizes'][0]))
        final_pop = int(round(results['focal_population_sizes'][-1]))
        change_pct = ((final_pop - initial_pop) / initial_pop * 100) if initial_pop > 0 else 0
        summary = (f"Initial: {initial_pop}  →  "
                  f"Final: {final_pop}  "
                  f"({change_pct:+.1f}% change)")
        ax.text(0.5, -0.15, summary, transform=ax.transAxes,
               fontsize=11, ha='center', style='italic')

    plt.tight_layout()

    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return image_base64


@app.route('/save_run', methods=['POST'])
def save_run():
    """Save a simulation run for comparison"""
    try:
        data = request.json
        run_name = data.get('name', f"Run {len(simulation_history) + 1}")

        # Store the run
        simulation_history.append({
            'id': len(simulation_history),
            'name': run_name,
            'timestamp': datetime.now().isoformat(),
            'results': data.get('results'),
            'parameters': data.get('parameters'),
            'plots': data.get('plots')
        })

        return jsonify({
            'success': True,
            'run_id': len(simulation_history) - 1,
            'total_runs': len(simulation_history)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/get_saved_runs', methods=['GET'])
def get_saved_runs():
    """Get list of saved simulation runs"""
    runs = [{
        'id': run['id'],
        'name': run['name'],
        'timestamp': run['timestamp'],
        'initial_pop': run['parameters'].get('focal_population', 'N/A'),
        'years': run['parameters'].get('simulation_years', 'N/A'),
        'final_pop': int(run['results']['focal_population_sizes'][-1]) if run['results'].get('focal_population_sizes') else 'N/A'
    } for run in simulation_history]

    return jsonify({'success': True, 'runs': runs})


@app.route('/delete_run/<int:run_id>', methods=['DELETE'])
def delete_run(run_id):
    """Delete a saved simulation run"""
    try:
        global simulation_history
        simulation_history = [run for run in simulation_history if run['id'] != run_id]
        # Reassign IDs
        for i, run in enumerate(simulation_history):
            run['id'] = i
        return jsonify({'success': True, 'total_runs': len(simulation_history)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/compare_runs', methods=['POST'])
def compare_runs():
    """Generate comparison visualization for selected runs"""
    try:
        data = request.json
        run_ids = data.get('run_ids', [])

        if not run_ids or len(run_ids) < 2:
            return jsonify({'success': False, 'error': 'Please select at least 2 runs to compare'}), 400

        # Get selected runs
        selected_runs = [run for run in simulation_history if run['id'] in run_ids]

        if len(selected_runs) < 2:
            return jsonify({'success': False, 'error': 'Invalid run IDs'}), 400

        # Generate comparison plot
        comparison_plot = generate_comparison_plot(selected_runs)

        # Generate summary statistics
        comparison_data = generate_comparison_summary(selected_runs)

        return jsonify({
            'success': True,
            'comparison_plot': comparison_plot,
            'comparison_data': comparison_data
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def generate_comparison_plot(runs):
    """Generate a comparison plot showing multiple simulation runs"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    colors = plt.cm.tab10(range(len(runs)))

    # Plot 1: Population over time
    for i, run in enumerate(runs):
        results = run['results']
        days_in_years = [d / 365 for d in results['days']]
        ax1.plot(days_in_years, results['focal_population_sizes'],
                linewidth=2.5, label=run['name'], color=colors[i],
                marker='o', markersize=3, alpha=0.8)

    ax1.set_title('Population Comparison Across Runs', fontsize=16, fontweight='bold', pad=15)
    ax1.set_xlabel('Years', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Population Size', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10, loc='best', frameon=True, shadow=True)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # Plot 2: Summary bar chart
    run_names = [run['name'] for run in runs]
    initial_pops = [run['results']['focal_population_sizes'][0] for run in runs]
    final_pops = [run['results']['focal_population_sizes'][-1] for run in runs]

    x = range(len(runs))
    width = 0.35

    ax2.bar([i - width/2 for i in x], initial_pops, width, label='Initial Population',
            color='#8ba3c7', alpha=0.9, edgecolor='black')
    ax2.bar([i + width/2 for i in x], final_pops, width, label='Final Population',
            color='#1e3a5f', alpha=0.9, edgecolor='black')

    ax2.set_title('Initial vs Final Population', fontsize=16, fontweight='bold', pad=15)
    ax2.set_ylabel('Population Size', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(run_names, rotation=45, ha='right')
    ax2.legend(fontsize=10, loc='best', frameon=True, shadow=True)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')

    plt.tight_layout()

    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return image_base64


def generate_comparison_summary(runs):
    """Generate summary statistics for comparison"""
    comparison = []

    for run in runs:
        results = run['results']
        params = run['parameters']

        initial_pop = results['focal_population_sizes'][0]
        final_pop = results['focal_population_sizes'][-1]
        change = final_pop - initial_pop
        change_pct = (change / initial_pop * 100) if initial_pop > 0 else 0

        comparison.append({
            'name': run['name'],
            'timestamp': run['timestamp'],
            'initial_population': round(initial_pop, 1),
            'final_population': round(final_pop, 1),
            'change': round(change, 1),
            'change_percent': round(change_pct, 1),
            'total_births': results.get('total_births', 0),
            'kitten_survival_rate': round(results.get('kitten_survival_rate', 0) * 100, 1),
            'years': params.get('simulation_years', 'N/A'),
            'females_amh_pct': params.get('pct_females_amh', 0),
            'females_spayed_pct': params.get('pct_females_spayed', 0),
            'males_neutered_pct': params.get('pct_males_neutered', 0),
            'litters_per_year': params.get('litters_per_year', 'N/A'),
            'arrivals_per_year': params.get('arrivals_per_year', 0),
            'departures_per_year': params.get('departures_per_year', 0)
        })

    return comparison


@app.route('/export_comparison', methods=['POST'])
def export_comparison():
    """Export comparison data to CSV"""
    try:
        data = request.json
        run_ids = data.get('run_ids', [])

        if not run_ids:
            return jsonify({'success': False, 'error': 'No runs selected'}), 400

        # Get selected runs
        selected_runs = [run for run in simulation_history if run['id'] in run_ids]

        if not selected_runs:
            return jsonify({'success': False, 'error': 'Invalid run IDs'}), 400

        # Generate comparison data
        comparison_data = generate_comparison_summary(selected_runs)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Run Name', 'Timestamp', 'Initial Population', 'Final Population',
            'Change', 'Change %', 'Total Births', 'Kitten Survival %',
            'Years', 'Females AMH %', 'Females Spayed %',
            'Males Neutered %', 'Litters/Year', 'Arrivals/Year', 'Departures/Year'
        ])

        # Write data
        for row in comparison_data:
            writer.writerow([
                row['name'], row['timestamp'], row['initial_population'],
                row['final_population'], row['change'], row['change_percent'],
                row['total_births'], row['kitten_survival_rate'],
                row['years'],
                row['females_amh_pct'], row['females_spayed_pct'],
                row['males_neutered_pct'], row['litters_per_year'],
                row['arrivals_per_year'], row['departures_per_year']
            ])

        # Prepare file for download
        output.seek(0)
        bytes_output = io.BytesIO()
        bytes_output.write(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)

        return send_file(
            bytes_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'simulation_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)

    # Bind all interfaces automatically when the platform provides a PORT (Render,
    # Railway, Heroku, etc.); otherwise stay local-only for safety. For production
    # prefer a real WSGI server: gunicorn enhanced_simulation_ui:app --bind 0.0.0.0:$PORT
    port = int(os.environ.get('PORT', os.environ.get('CATSIM_PORT', '5001')))
    default_host = '0.0.0.0' if os.environ.get('PORT') else '127.0.0.1'
    host = os.environ.get('CATSIM_HOST', default_host)
    debug = os.environ.get('CATSIM_DEBUG', '0') == '1'

    print("="*70)
    print(" ENHANCED POPULATION SIMULATION UI")
    print("="*70)
    print(f"\nStarting server on http://{host}:{port}")
    print("\nFeatures:")
    print("  • Estrous cycle modeling (16-day cycle, 7-day estrus)")
    print("  • Male attention / monopolization dynamics")
    print("  • AMH contraception (distinct from surgical sterilization)")
    print("  • Seasonal breeding (Jan-Sep)")
    print("  • 65-day gestation + 56-day (8-week) postpartum delay")
    print("  • Fixed biology from biological_parameters.py; management params via sliders")
    print("="*70)

    app.run(debug=debug, host=host, port=port)
