#!/usr/bin/env python3
"""
Enhanced Population Simulation UI with Detailed Biological Parameters
Includes estrous cycles, male monopolization, AMH contraception, and more
"""

from flask import Flask, render_template, request, jsonify
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from biological_parameters import DEFAULT_BIOLOGICAL_CONFIG

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main UI page with all biological parameter controls"""
    return render_template('enhanced_index.html', config=DEFAULT_BIOLOGICAL_CONFIG)


@app.route('/run_enhanced_simulation', methods=['POST'])
def run_enhanced_simulation():
    """Run simulation with detailed biological parameters"""
    try:
        data = request.json

        # Extract all parameters from UI
        params = {
            # Estrous cycle parameters
            'estrous_cycle_length': int(data.get('estrous_cycle_length', 21)),
            'estrus_length': int(data.get('estrus_length', 8)),

            # Maturity ages (now accept decimal values)
            'female_maturity_min_months': float(data.get('female_maturity_min_months', 6.0)),
            'female_maturity_max_months': float(data.get('female_maturity_max_months', 8.0)),
            'male_maturity_months': float(data.get('male_maturity_months', 12.0)),

            # Breeding season
            'breeding_season_start_month': int(data.get('breeding_season_start_month', 1)),
            'breeding_season_end_month': int(data.get('breeding_season_end_month', 9)),

            # Male monopolization
            'monopolization_intact_days': int(data.get('monopolization_intact_days', 8)),
            'monopolization_amh_days': int(data.get('monopolization_amh_days', 21)),

            # Pregnancy
            'gestation_period_days': int(data.get('gestation_period_days', 63)),
            'postpartum_delay_days': int(data.get('postpartum_delay_days', 21)),

            # Breeding parameters
            'litters_per_year': float(data.get('litters_per_year', 2.0)),
            'mean_litter_size': float(data.get('mean_litter_size', 4.0)),
            'sd_litter_size': float(data.get('sd_litter_size', 1.5)),
            'max_litter_size': int(data.get('max_litter_size', 8)),

            # Fertility control
            'pct_females_amh': float(data.get('pct_females_amh', 0)),
            'pct_females_spayed': float(data.get('pct_females_spayed', 0)),
            'pct_males_neutered': float(data.get('pct_males_neutered', 0)),

            # Simulation settings
            'simulation_years': int(data.get('simulation_years', 10)),
            'simulation_days': int(data.get('simulation_years', 10)) * 365,

            # Focal population (managed with fertility control)
            'focal_population': int(data.get('focal_population', 50)),
            'focal_carrying_capacity': int(data.get('focal_carrying_capacity', 200)),

            # Neighborhood population (unmanaged source of immigrants)
            'neighborhood_population': int(data.get('neighborhood_population', 200)),
            'neighborhood_carrying_capacity': int(data.get('neighborhood_carrying_capacity', 800)),

            # Dispersal parameters
            'dispersal_rate': float(data.get('dispersal_rate', 2.0)),  # % per 6 months
            'immigration_rate': float(data.get('immigration_rate', 2.0)),  # % per 6 months
            'litter_abandonment_per_year': int(data.get('litter_abandonment_per_year', 2)),

            # Kitten mortality parameters (density-dependent)
            'base_kitten_mortality': float(data.get('base_kitten_mortality', 0.75)),  # Low density mortality
            'high_density_mortality': float(data.get('high_density_mortality', 0.87)),  # High density mortality

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

        return jsonify({
            'success': True,
            'results': results,
            'plots': plot_data,
            'parameters_used': params
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def generate_mock_results(params):
    """Generate mock results for testing UI with focal and neighborhood populations"""
    days = params['simulation_days']
    sample_points = min(days // 30, 365)  # Sample monthly, max 365 points
    sample_points = max(sample_points, 10)  # Minimum 10 points

    # Get population parameters
    focal_pop = params.get('focal_population', params.get('initial_adult_population', 50))
    neighborhood_pop = params.get('neighborhood_population', 200)
    focal_capacity = params.get('focal_carrying_capacity', params.get('carrying_capacity', 200))
    neighborhood_capacity = params.get('neighborhood_carrying_capacity', 800)

    # Dispersal rates (convert from per-6-months to per-day)
    dispersal_rate_daily = params.get('dispersal_rate', 2.0) / 100.0 / 182.5  # 2% per 6 months
    immigration_rate_daily = params.get('immigration_rate', 2.0) / 100.0 / 182.5
    litter_abandonment_yearly = params.get('litter_abandonment_per_year', 2)
    abandonment_rate_daily = litter_abandonment_yearly * 3.0 / 365.0  # ~3 kittens per litter

    results = {
        'days': list(range(0, days, max(days // sample_points, 1))),
        'focal_population_sizes': [],
        'neighborhood_population_sizes': [],
        'population_sizes': [],  # Total (for backwards compatibility)
        'females_in_estrus': [],
        'pregnant_females': [],
        'males_monopolizing': [],
        'immigrants': [],
        'emigrants': [],
        'abandoned_kittens': [],
        'total_births': 0,
        'total_immigrants': 0,
        'total_emigrants': 0,
        'total_abandoned': 0,
        'kitten_survival_rate': 0.25,
    }

    # Track populations over time
    current_focal = focal_pop
    current_neighborhood = neighborhood_pop

    for day in results['days']:
        # === FOCAL POPULATION (with fertility control) ===

        # Population grows then stabilizes towards capacity
        growth_factor = min(1.0, day / (days * 0.3))
        target_focal = int(focal_pop * (1 + growth_factor * 0.5))
        target_focal = min(target_focal, focal_capacity)

        # Apply fertility control effect (only to focal population)
        fc_effect = (
            params['pct_females_spayed'] * 0.5 +
            params['pct_males_neutered'] * 0.3 +
            params['pct_females_amh'] * 0.4
        ) / 100.0

        focal_with_control = int(target_focal * (1 - fc_effect * 0.5))

        # Calculate daily immigration from neighborhood
        immigrants_today = int(current_neighborhood * immigration_rate_daily)
        abandoned_today = abandonment_rate_daily if day > 0 else 0

        # Calculate daily emigration from focal
        emigrants_today = int(current_focal * dispersal_rate_daily * 0.5)  # Some leave

        # Update focal population
        current_focal = focal_with_control + immigrants_today + int(abandoned_today) - emigrants_today
        current_focal = max(0, min(current_focal, focal_capacity))

        results['focal_population_sizes'].append(current_focal)
        results['immigrants'].append(immigrants_today)
        results['emigrants'].append(emigrants_today)
        results['abandoned_kittens'].append(int(abandoned_today))

        results['total_immigrants'] += immigrants_today
        results['total_emigrants'] += emigrants_today
        results['total_abandoned'] += int(abandoned_today)

        # === NEIGHBORHOOD POPULATION (no fertility control, stable) ===

        # Neighborhood stays relatively stable at capacity
        current_neighborhood = neighborhood_pop + int((neighborhood_capacity - neighborhood_pop) * 0.1)
        results['neighborhood_population_sizes'].append(current_neighborhood)

        # === COMBINED STATISTICS ===

        total_pop = current_focal + current_neighborhood
        results['population_sizes'].append(total_pop)

        # Estimate females in estrus (only focal population tracked in detail)
        fertile_females = current_focal // 2 * (1 - params['pct_females_spayed'] / 100)
        estrus_females = int(fertile_females * (params['estrus_length'] / params['estrous_cycle_length']))
        results['females_in_estrus'].append(estrus_females)

        # Estimate pregnant females (63-day gestation)
        pregnant = int(fertile_females * 0.3)  # Rough estimate
        results['pregnant_females'].append(pregnant)

        # Estimate monopolizing males
        monopolizing = int(estrus_females * 0.7)  # Most estrus females have a male
        results['males_monopolizing'].append(monopolizing)

    # Calculate total births (affected by fertility control)
    avg_litters_per_year = params.get('litters_per_year', 2.0)
    time_years = days / 365.0
    total_births_no_control = int(focal_pop / 2 * avg_litters_per_year * time_years * params['mean_litter_size'])
    results['total_births'] = int(total_births_no_control * (1 - fc_effect * 0.8))

    return results


def generate_enhanced_plots(results):
    """Generate population plot only"""

    fig, ax = plt.subplots(figsize=(12, 6))

    days_in_years = [d / 365 for d in results['days']]

    # Only plot: Focal vs Neighborhood Populations
    if 'focal_population_sizes' in results:
        ax.plot(days_in_years, results['focal_population_sizes'], 'b-', linewidth=3,
                label='Focal Population (Managed)', marker='o', markersize=4)
        ax.plot(days_in_years, results['neighborhood_population_sizes'], 'orange', linewidth=3,
                label='Neighborhood Population (Unmanaged)', marker='s', markersize=4)
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
        summary = (f"Initial Focal: {results['focal_population_sizes'][0]:,}  →  "
                  f"Final Focal: {results['focal_population_sizes'][-1]:,}  "
                  f"({((results['focal_population_sizes'][-1] - results['focal_population_sizes'][0]) / results['focal_population_sizes'][0] * 100):+.1f}% change)")
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
