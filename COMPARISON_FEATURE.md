# Simulation Comparison Feature

## Overview
The cat population simulation now includes a comprehensive comparison feature that allows you to save, compare, and analyze multiple simulation runs side-by-side.

## Features Added

### 1. Save Simulation Runs
- After running any simulation, you can save it for later comparison
- Enter a custom name or use the auto-generated timestamp name
- All parameters and results are stored for each run

### 2. View Saved Runs
- Click "View Saved Runs" button to see all your saved simulations
- Each saved run shows:
  - Run name
  - Initial and final population
  - Simulation duration
  - Timestamp
- Delete individual runs or clear all at once

### 3. Compare Multiple Runs
- Select 2 or more saved runs using checkboxes
- Click "Compare Selected Runs" to generate comparison visualizations
- View side-by-side comparison charts showing:
  - Population trajectories over time (line graph)
  - Initial vs final population (bar chart)

### 4. Comparison Table
- Detailed statistics table showing:
  - Initial and final populations
  - Population change (absolute and percentage)
  - Total births
  - Kitten survival rate
  - All fertility control parameters (AMH %, Spayed %, Neutered %)
  - Litters per year
  - Arrivals and departures per year

### 5. Export to CSV
- Select one or more runs
- Click "Export to CSV" to download comparison data
- CSV includes all key metrics and parameters
- Perfect for further analysis in Excel, R, or Python

## How to Use

### Basic Workflow
1. **Run a simulation** with your desired parameters
2. **Save the run** by entering a name and clicking "Save for Comparison"
3. **Repeat steps 1-2** with different parameters (e.g., varying AMH percentages)
4. **Click "View Saved Runs"** to access the comparison interface
5. **Select runs to compare** using checkboxes
6. **Click "Compare Selected Runs"** to visualize differences
7. **Export to CSV** if you want to analyze data elsewhere

### Example Use Cases

#### Comparing Contraception Methods
- Run 1: Baseline (no interventions)
- Run 2: 30% females on AMH
- Run 3: 30% females spayed
- Run 4: 30% males neutered
- Compare all 4 to see which strategy is most effective

#### Dose-Response Analysis
- Run 1: 10% AMH coverage
- Run 2: 25% AMH coverage
- Run 3: 50% AMH coverage
- Run 4: 75% AMH coverage
- Compare to understand the relationship between coverage and population change

#### Intervention Timing
- Run 1: One-time intervention at start
- Run 2: Yearly interventions
- Compare to see the impact of intervention timing

#### Parameter Sensitivity
- Vary male breeding capacity, litters per year, mortality rates, etc.
- Compare to understand which parameters most affect outcomes

## Technical Details

### Backend (enhanced_simulation_ui.py)
- `simulation_history`: In-memory storage for saved runs
- `/save_run`: POST endpoint to save simulation results
- `/get_saved_runs`: GET endpoint to retrieve all saved runs
- `/delete_run/<id>`: DELETE endpoint to remove a run
- `/compare_runs`: POST endpoint to generate comparison visualizations
- `/export_comparison`: POST endpoint to export data as CSV

### Frontend (enhanced_index.html)
- Comparison UI container with saved runs list
- JavaScript functions for managing saved runs
- Interactive checkboxes for run selection
- Dynamic table generation for comparison results
- CSV export with automatic file download

### Data Persistence
Currently, saved runs are stored in memory and will be lost when the server restarts. For production use, consider:
- Adding a database (SQLite, PostgreSQL, etc.)
- Implementing user accounts and authentication
- Saving to JSON files on disk

## Limitations
- Runs are stored in server memory (lost on restart)
- No user authentication (all users share the same run history)
- Maximum runs limited by available memory
- No pagination for large numbers of runs

## Future Enhancements
- Persistent storage (database or file-based)
- User accounts and private run histories
- More comparison metrics (peak population, time to stability, etc.)
- Additional export formats (Excel, JSON, PDF reports)
- Statistical analysis (t-tests, effect sizes, etc.)
- Parameter sweep tools for automated comparison generation
