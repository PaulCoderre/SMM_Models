import xarray as xr
import os
import pandas as pd
import cftime
import sys
import glob
import shutil
import subprocess
import re
import shutil
import sys

# Define the inputs
forcings_directory = '../easymore_run'  # directory containing results from easymore
model_directory = '../model'  # directory containing HYPE model files
hype_executable = './hype'  # command line argument to run HYPE
runs_per_script = 3
file_pattern = "*.nc"

print('Program Running')

# Get the current working directory
current_directory = os.getcwd()

# Access the environment variable set by the shell script
directory_index = os.getenv("SLURM_ARRAY_TASK_ID")
if len(sys.argv) != 2:
    print("Usage: python run_easymore.py <index>")
    sys.exit(1)

run_number = int(sys.argv[1])
print(f'Run number= {run_number}')

# debug
#run_number = 1

# Get a list of each directory in the specified directory
directory_list = sorted([d for d in os.listdir(forcings_directory) if os.path.isdir(os.path.join(forcings_directory, d))])
# Remove .ipynb_checkpoints from the list if present
if '.ipynb_checkpoints' in directory_list:
    directory_list.remove('.ipynb_checkpoints')
print(directory_list)

# Define ranges 
low_range = run_number * runs_per_script - runs_per_script
upper_range = run_number * runs_per_script

print(f'Run from {low_range} to {upper_range}')
    
# Slice the directory list based on the specified range
directory_subset = directory_list[low_range:upper_range]

working_directory = f'working_directory_{run_number}'
results_directory = f'results_{run_number}'  # will be created if not present 

# Create the working directory if it doesn't exist
if not os.path.exists(working_directory):
    os.makedirs(working_directory)

# Copy all files from the source directory to the working directory
for file_name in os.listdir(model_directory):
    source_file = os.path.join(model_directory, file_name)
    if os.path.isfile(source_file):
        shutil.copy(source_file, working_directory)
        
# Create the results directory if it doesn't exist
if not os.path.exists(results_directory):
    os.makedirs(results_directory)

# Function to correct invalid dates
def correct_invalid_dates(date_str):
    try:
        return pd.to_datetime(date_str)
    except ValueError:
        return pd.NaT
    
# Iterate through each directory in the directory_subset
for directory in directory_subset:
    # Exclude .ipynb_checkpoints directory
    if directory == ".ipynb_checkpoints":
        continue
    directory_path = os.path.join(forcings_directory, directory)
    if os.path.isdir(directory_path):
        # Open and concatenate the files using open_mfdataset
        combined_dataset = xr.open_mfdataset(os.path.join(directory_path, file_pattern), combine="by_coords")
        
        # Extract the number from the directory name
        directory_number = re.findall(r'\d+', directory)[0]
        
        print(f'Beginning run for cmip: {directory_number}')
        
        # Extract forcings as dataframes
        precipitation_df = combined_dataset['precipitation'].to_dataframe()  # in kg/m2/s
        tmax_df = combined_dataset['max_temperature'].to_dataframe()  # in kelvin
        tmin_df = combined_dataset['min_temperature'].to_dataframe()  # in kelvin

        # Pivot forcing dataframes to match HYPE input format
        precipitation_pivoted = precipitation_df.reset_index().pivot(index='time', columns='ID', values='precipitation')
        tmax_pivoted = tmax_df.reset_index().pivot(index='time', columns='ID', values='max_temperature')
        tmin_pivoted = tmin_df.reset_index().pivot(index='time', columns='ID', values='min_temperature')

        # Convert column headers to integers
        precipitation_pivoted.columns = [int(col) for col in precipitation_pivoted.columns]
        tmax_pivoted.columns = [int(col) for col in tmax_pivoted.columns]
        tmin_pivoted.columns = [int(col) for col in tmin_pivoted.columns]
     
        print(f'Forcings reformated for cmip: {directory_number}')

        # Convert tmax and tmin from kelvin to celsius
        tmax_celsius = tmax_pivoted - 273.15
        tmin_celsius = tmin_pivoted - 273.15

        # Write tobs as the mean of tmax and tmin
        tobs_celsius = (tmax_celsius + tmin_celsius) / 2

        # Convert p from kg/m2/s to mm/day
        precipitation_mm = precipitation_pivoted * 3600 * 24 / 1000 * 1000  # convert s to day, divide by density 1000 kg/m3, multiply by 1000mm in 1 m

        os.chdir(working_directory)
        
        # Convert cftime objects to string format
        precipitation_mm.index = [date.strftime('%Y-%m-%d') for date in precipitation_mm.index]
        tmax_celsius.index = [date.strftime('%Y-%m-%d') for date in tmax_celsius.index]
        tmin_celsius.index = [date.strftime('%Y-%m-%d') for date in tmin_celsius.index]
        tobs_celsius.index = [date.strftime('%Y-%m-%d') for date in tobs_celsius.index]

        # Function to check if a date string is invalid (02-29 or 02-30)
        def is_invalid_date(date_str):
            try:
                month_day = date_str[5:10]  # Extract MM-DD part of the date string
                if month_day in ['02-29', '02-30']: 
                    print("Invalid dates removed")
                    return True
                return False
            except:
                return True  # Treat any parsing issue as invalid

            # Reset the index to make it a column
        precipitation_mm.reset_index(inplace=True)
        tmax_celsius.reset_index(inplace=True)
        tmin_celsius.reset_index(inplace=True)
        tobs_celsius.reset_index(inplace=True)
        
        # Apply the function to filter out invalid dates
        invalid_dates = precipitation_mm['index'].apply(is_invalid_date)

        precipitation_mm_valid = precipitation_mm[~invalid_dates].copy() 
        tmax_celsius_valid = tmax_celsius[~invalid_dates].copy() 
        tmin_celsius_valid = tmin_celsius[~invalid_dates].copy() 
        tobs_celsius_valid = tobs_celsius[~invalid_dates].copy() # Keep only rows with valid dates
        
        
        # Convert the valid dates to datetime format
        precipitation_mm_valid['index'] = pd.to_datetime(precipitation_mm_valid['index'])
        tmax_celsius_valid['index'] = pd.to_datetime(tmax_celsius_valid['index'])
        tmin_celsius_valid['index'] = pd.to_datetime(tmin_celsius_valid['index'])
        tobs_celsius_valid['index'] = pd.to_datetime(tobs_celsius_valid['index'])

        # Set the valid dates as the index
        precipitation_mm_valid.set_index('index', inplace=True)
        tmax_celsius_valid.set_index('index', inplace=True)
        tmin_celsius_valid.set_index('index', inplace=True)
        tobs_celsius_valid.set_index('index', inplace=True)

        # set columns to numeric
        precipitation_mm_valid = precipitation_mm_valid.apply(pd.to_numeric, errors='coerce')
        tmax_celsius_valid = tmax_celsius_valid.apply(pd.to_numeric, errors='coerce')
        tmin_celsius_valid = tmin_celsius_valid.apply(pd.to_numeric, errors='coerce')
        tobs_celsius_valid = tobs_celsius_valid.apply(pd.to_numeric, errors='coerce')
        
        # Find the minimum and maximum dates in the DataFrame index
        min_date = precipitation_mm_valid.index.min()
        max_date = precipitation_mm_valid.index.max()

        # Ensure max_date includes the entire day of December 31
        # Add one day to max_date and then subtract one second to ensure we cover the entire last day
        max_date = pd.Timestamp(year=max_date.year, month=12, day=31)

        # Calculate the full expected date range, including both min_date and max_date
        expected_dates = pd.date_range(start=min_date, end=max_date, freq='D')

        # Identify missing dates by checking which expected dates are not in the DataFrame index
        missing_dates = expected_dates[~expected_dates.isin(precipitation_mm_valid.index)]
        
        if not missing_dates.empty:
            precipitation_mm_valid = precipitation_mm_valid.reindex(expected_dates)
            precipitation_mm_valid = precipitation_mm_valid.fillna(method='ffill').fillna(method='bfill')
            precipitation_mm_valid = precipitation_mm_valid.dropna()

            tmax_celsius_valid = tmax_celsius_valid.reindex(expected_dates)
            tmax_celsius_valid = tmax_celsius_valid.fillna(method='ffill').fillna(method='bfill')
            tmax_celsius_valid = tmax_celsius_valid.dropna()

            tmin_celsius_valid = tmin_celsius_valid.reindex(expected_dates)
            tmin_celsius_valid = tmin_celsius_valid.fillna(method='ffill').fillna(method='bfill')
            tmin_celsius_valid = tmin_celsius_valid.dropna()

            tobs_celsius_valid = tobs_celsius_valid.reindex(expected_dates)
            tobs_celsius_valid = tobs_celsius_valid.fillna(method='ffill').fillna(method='bfill')
            tobs_celsius_valid = tobs_celsius_valid.dropna()

            print("Missing dates filled")
        else:
            print("No missing dates")

            # Rename the index to 'time'
        precipitation_mm_valid = precipitation_mm_valid.rename_axis('time')
        tmax_celsius_valid = tmax_celsius_valid.rename_axis('time')
        tmin_celsius_valid = tmin_celsius_valid.rename_axis('time')
        tobs_celsius_valid = tobs_celsius_valid.rename_axis('time')
        
        
 
        # Save the DataFrame to a tab-separated text file
        precipitation_mm_valid.to_csv('Pobs.txt', sep='\t')
        tmax_celsius_valid.to_csv('TMAXobs.txt', sep='\t')
        tmin_celsius_valid.to_csv('TMINobs.txt', sep='\t')
        tobs_celsius_valid.to_csv('Tobs.txt', sep='\t')

        # Run HYPE
        try:
            subprocess.run(hype_executable, check=True)
            print("HYPE program executed successfully.")
        except subprocess.CalledProcessError as e:
            print("Error running HYPE program:", e)
            
        os.chdir(current_directory)

        # Get a list of all files in the working directory
        files = os.listdir(working_directory)
        
        # Find the name of any text file starting with "00"
        matching_files = [file for file in files if file.startswith("00") and file.endswith(".txt")]

        # Rename each file by adding the directory name as a prefix
        for file in matching_files:
            # Construct the new file name with the directory name as a prefix
            new_file_name = os.path.join(working_directory, f"{directory_number}_{file}")

            # Rename the file
            os.rename(os.path.join(working_directory, file), new_file_name)
        
                # Move files starting with directory_number in working_directory to results_directory
        for file in os.listdir(working_directory):
            if file.startswith(directory_number):
                shutil.move(os.path.join(working_directory, file), os.path.join(results_directory, file))
                
        print(f'End of run for cmip: {directory_number}')

# Delete the working directory
shutil.rmtree(working_directory)