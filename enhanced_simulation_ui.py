#!/usr/bin/env python3
"""
Enhanced Population Simulation UI with Detailed Biological Parameters
Includes estrous cycles, male monopolization, AMH contraception, and more
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from biological_parameters import DEFAULT_BIOLOGICAL_CONFIG
from datetime import datetime
import csv

app = Flask(__name__)

# Store simulation runs for comparison
simulation_history = []

@app.route('/')
def index():
    """Render the main UI page with all biological parameter controls"""
    return render_template('enhanced_index.html', config=DEFAULT_BIOLOGICAL_CONFIG)


@app.route('/run_enhanced_simulation', methods=['POST'])
def run_enhanced_simulation():
    """Run simulation with detailed biological parameters"""
    try:
        data = request.json

        # HARDCODED BIOLOGICAL PARAMETERS (based on research data)
        # These are no longer adjustable via UI to ensure biological accuracy

        # Estrous cycle: Full cycle = estrus duration + interval between estrous periods
        # Estrus duration: 7.4 days (SD = 3.7; range 2–19 days)
        # Interval between estrous periods: 9.0 days (SD 7.6; range 4–22 days)
        # Complete cycle: 7.4 + 9.0 = 16.4 days
        estrous_cycle_length = 16  # Round to 16 days for simplicity
        estrus_length = 7  # Round to 7 days for simplicity

        # Female sexual maturity: Average age at sexual maturity: 8.5 months (SD = 2.0; range 4-18 months)
        female_maturity_mean_months = 8.5
        female_maturity_sd_months = 2.0
        female_maturity_min_months = 4.0
        female_maturity_max_months = 18.0

        # Male sexual maturity: Average age: 10 months (range 7-12 months)
        male_maturity_mean_months = 10.0
        male_maturity_min_months = 7.0
        male_maturity_max_months = 12.0

        # Gestation period: Fixed at 65 days
        gestation_period_days = 65

        # Postpartum delay: Fixed at 8 weeks (56 days)
        postpartum_delay_days = 56

        # Litter size: Mean 4 kittens (SD = 1.9; range 1-9)
        mean_litter_size = 4.0
        sd_litter_size = 1.9
        min_litter_size = 1
        max_litter_size = 9

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

            # Breeding season (hardcoded - year-round breeding)
            'breeding_season_start_month': 1,
            'breeding_season_end_month': 12,

            # Male breeding capacity (still adjustable)
            'male_breeding_capacity_per_day': float(data.get('male_breeding_capacity_per_day', 3.0)),
            'monopolization_amh_days': int(data.get('monopolization_amh_days', 15)),

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

            # Focal population (still adjustable)
            'focal_population': int(data.get('focal_population', 50)),
            'male_percentage': float(data.get('male_percentage', 50)),
            'focal_carrying_capacity': int(data.get('focal_carrying_capacity', 200)),

            # Population dynamics (still adjustable)
            'arrivals_per_year': int(data.get('arrivals_per_year', 10)),
            'departures_per_year': int(data.get('departures_per_year', 10)),

            # Mortality parameters
            'adult_mortality_annual': float(data.get('adult_mortality_annual', 10)),
            # Kitten mortality (hardcoded - density-dependent)
            'base_kitten_mortality': 0.75,  # 75% at low density
            'high_density_mortality': 0.87,  # 87% at carrying capacity

            # Legacy support
            'initial_adult_population': int(data.get('initial_adult_population',
                                                    data.get('focal_population', 50))),
            'initial_female_percentage': float(data.get('initial_female_percentage', 50)),
            'carrying_capacity': int(data.get('carrying_capacity',
                                             data.get('focal_carrying_capacity', 200))),
        }

        # Run working simulation via adapter
        from working_simulation_adapter import run_adapted_simulation
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


def generate_mock_results(params):
    """Generate mock results for testing UI"""
    days = params['simulation_days']
    sample_points = min(days // 30, 365)  # Sample monthly, max 365 points
    sample_points = max(sample_points, 10)  # Minimum 10 points

    # Get population parameters
    focal_pop = params.get('focal_population', params.get('initial_adult_population', 50))
    focal_capacity = params.get('focal_carrying_capacity', params.get('carrying_capacity', 200))

    # Population dynamics
    arrivals_per_year = params.get('arrivals_per_year', 10)
    departures_per_year = params.get('departures_per_year', 10)
    arrivals_per_day = arrivals_per_year / 365.0
    departures_per_day = departures_per_year / 365.0

    results = {
        'days': list(range(0, days, max(days // sample_points, 1))),
        'focal_population_sizes': [],
        'population_sizes': [],
        'females_in_estrus': [],
        'pregnant_females': [],
        'males_monopolizing': [],
        'arrivals': [],
        'departures': [],
        'total_births': 0,
        'total_arrivals': 0,
        'total_departures': 0,
        'kitten_survival_rate': 0.25,
    }

    # Track population over time
    current_pop = focal_pop

    for day in results['days']:
        # Population grows then stabilizes towards capacity
        growth_factor = min(1.0, day / (days * 0.3))
        target_pop = int(focal_pop * (1 + growth_factor * 0.5))
        target_pop = min(target_pop, focal_capacity)

        # Apply fertility control effect
        fc_effect = (
            params.get('pct_females_spayed', 0) * 0.5 +
            params.get('pct_males_neutered', 0) * 0.3 +
            params.get('pct_females_amh', 0) * 0.4
        ) / 100.0

        pop_with_control = int(target_pop * (1 - fc_effect * 0.5))

        # Apply arrivals and departures
        arrivals_today = arrivals_per_day
        departures_today = departures_per_day

        # Update population
        current_pop = pop_with_control + arrivals_today - departures_today
        current_pop = max(0, min(current_pop, focal_capacity))

        results['focal_population_sizes'].append(current_pop)
        results['population_sizes'].append(current_pop)
        results['arrivals'].append(arrivals_today)
        results['departures'].append(departures_today)

        results['total_arrivals'] += arrivals_today
        results['total_departures'] += departures_today

        # Estimate females in estrus (7 days out of 16-day cycle)
        fertile_females = current_pop // 2 * (1 - params.get('pct_females_spayed', 0) / 100)
        estrus_females = int(fertile_females * (7 / 16))
        results['females_in_estrus'].append(estrus_females)

        # Estimate pregnant females
        pregnant = int(fertile_females * 0.3)
        results['pregnant_females'].append(pregnant)

        # Estimate monopolizing males
        monopolizing = int(estrus_females * 0.7)
        results['males_monopolizing'].append(monopolizing)

    # Calculate total births
    avg_litters_per_year = params.get('litters_per_year', 2.0)
    time_years = days / 365.0
    total_births_no_control = int(focal_pop / 2 * avg_litters_per_year * time_years * params.get('mean_litter_size', 4))
    results['total_births'] = int(total_births_no_control * (1 - fc_effect * 0.8))

    return results


def generate_enhanced_plots(results):
    """Generate population plot"""

    fig, ax = plt.subplots(figsize=(12, 6))

    days_in_years = [d / 365 for d in results['days']]

    # Plot focal population
    if 'focal_population_sizes' in results:
        ax.plot(days_in_years, results['focal_population_sizes'], 'b-', linewidth=3,
                label='Focal Population', marker='o', markersize=4)
        ax.set_title('Population Dynamics Over Time', fontsize=18, fontweight='bold', pad=20)
    else:
        ax.plot(days_in_years, results['population_sizes'], 'b-', linewidth=3, marker='o', markersize=4)
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
            color='steelblue', alpha=0.8, edgecolor='black')
    ax2.bar([i + width/2 for i in x], final_pops, width, label='Final Population',
            color='coral', alpha=0.8, edgecolor='black')

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
            'Years', 'Females AMH %', 'Females Spayed %', 'Males Neutered %',
            'Litters/Year', 'Arrivals/Year', 'Departures/Year'
        ])

        # Write data
        for row in comparison_data:
            writer.writerow([
                row['name'], row['timestamp'], row['initial_population'],
                row['final_population'], row['change'], row['change_percent'],
                row['total_births'], row['kitten_survival_rate'], row['years'],
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
    import os
    os.makedirs('templates', exist_ok=True)

    print("="*70)
    print(" ENHANCED POPULATION SIMULATION UI")
    print("="*70)
    print("\nStarting server with detailed biological parameters...")
    print("Open your browser to: http://localhost:5001")
    print("\nNew features:")
    print("  • Estrous cycle modeling (21-day cycle, 8-day estrus)")
    print("  • Male monopolization dynamics")
    print("  • AMH contraception (distinct from surgical sterilization)")
    print("  • Seasonal breeding restrictions")
    print("  • 12-week pregnancy + postpartum delay")
    print("  • All parameters adjustable via sliders!")
    print("="*70)

    app.run(debug=True, host='0.0.0.0', port=5001)
