# Quick Start Guide - Comparison Feature

## Getting Started in 3 Minutes

### Step 1: Start the Server (10 seconds)
```bash
python3 enhanced_simulation_ui.py
```

Open your browser to: http://localhost:5001

### Step 2: Run Your First Simulation (30 seconds)
1. Adjust parameters in the left panel (or use defaults)
2. Click "Run Enhanced Simulation"
3. Wait for results to appear
4. Enter a name like "Baseline - No Intervention"
5. Click "Save for Comparison"

### Step 3: Run A Second Simulation (30 seconds)
1. Change a parameter (e.g., set "Females on AMH Contraceptive" to 50%)
2. Click "Run Enhanced Simulation"
3. Enter a name like "50% AMH Coverage"
4. Click "Save for Comparison"

### Step 4: Compare Results (30 seconds)
1. Click "View Saved Runs" button
2. Check the boxes next to both runs
3. Click "Compare Selected Runs"
4. View the comparison chart and statistics table

### Step 5: Export (Optional)
1. Keep your runs selected
2. Click "Export to CSV"
3. File will download automatically

## Example Comparison Scenarios

### Scenario 1: Contraceptive Efficacy Test
Compare AMH contraception vs surgical sterilization at the same coverage level.

**Run A: "AMH 40%"**
- Females on AMH Contraceptive: 40%
- All other parameters: default

**Run B: "Spayed 40%"**
- Females Spayed: 40%
- All other parameters: default

**Expected Results:**
- Spaying will show greater population reduction
- AMH will show more male monopolization dynamics
- Both will significantly reduce births compared to baseline

---

### Scenario 2: Intervention Timing
Compare one-time vs yearly interventions.

**Run A: "One-time 30% AMH"**
- Fertility Control Timing: One-time (at start)
- Females on AMH: 30%

**Run B: "Yearly 30% AMH"**
- Fertility Control Timing: Yearly (ongoing)
- Females on AMH: 30%

**Expected Results:**
- Yearly interventions will maintain higher coverage over time
- Better long-term population control with ongoing interventions

---

### Scenario 3: Dose-Response Curve
Understand relationship between coverage and population control.

Create 5 runs with increasing AMH coverage:
- Run 1: 0% AMH (baseline)
- Run 2: 20% AMH
- Run 3: 40% AMH
- Run 4: 60% AMH
- Run 5: 80% AMH

**Expected Results:**
- Non-linear dose-response relationship
- Identify minimum effective coverage level
- See diminishing returns at high coverage

---

### Scenario 4: Male vs Female Interventions
Compare targeting different sexes.

**Run A: "40% Females Spayed"**
- Females Spayed: 40%

**Run B: "40% Males Neutered"**
- Males Neutered: 40%

**Expected Results:**
- Female interventions typically more effective
- Male neutering impact depends on male:female ratio

---

## Tips for Effective Comparisons

1. **Change One Variable at a Time**
   - Makes it easier to understand cause and effect
   - Isolates the impact of specific parameters

2. **Use Descriptive Names**
   - Good: "AMH 50% - 10yr - CC200"
   - Bad: "Run 3"

3. **Run Multiple Replicates**
   - Some stochasticity in the model
   - Run same parameters 2-3 times to check consistency

4. **Keep a Log**
   - Export results regularly
   - Document interesting findings
   - Track what parameters you've tested

5. **Start with Extremes**
   - Test 0% vs 100% interventions first
   - Helps bound the possible outcomes
   - Then fill in with intermediate values

## Keyboard Shortcuts & Tips

- **Shift + Click**: Select multiple consecutive runs
- **Ctrl/Cmd + Click**: Select non-consecutive runs
- **Double-click run name**: Quick view of that run's parameters (future feature)

## Troubleshooting

### "No simulation results to save"
- You need to run a simulation first before saving
- Click "Run Enhanced Simulation" button

### Comparison chart looks cluttered
- Compare fewer runs at once (2-4 recommended)
- Delete old runs you no longer need

### Can't find my saved runs
- Runs are stored in server memory
- They're lost when you restart the server
- Export important results to CSV

### Runs disappeared after restart
- This is expected - runs are not persistent
- For production use, implement database storage
- See COMPARISON_FEATURE.md for details

## Advanced: Bulk Comparison Workflow

For systematic parameter exploration:

1. Create a spreadsheet with parameter combinations
2. Run each combination and save with systematic names
3. Export all results to CSV
4. Analyze in Excel, R, or Python
5. Identify optimal parameter ranges
6. Present findings with comparison charts

Example naming convention:
- `AMH_{pct}_Spay_{pct}_Male_{pct}_Arr_{n}_Dep_{n}`
- `AMH_30_Spay_0_Male_10_Arr_10_Dep_5`

This makes it easy to parse filenames and automate analysis.
