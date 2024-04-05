#!/usr/bin/env python

import subprocess
import os
import pandas as pd
import numpy as np
from typing import Tuple

def update_adj(array: np.ndarray, dataframe: pd.DataFrame, ranges: pd.DataFrame):
    # Iterate through columns in the DataFrame
    for column_name in dataframe.columns:
        # Extract low_bound and upper_bound values for the current column_name
        low_bound = ranges.at[column_name, 'low_bound']
        upper_bound = ranges.at[column_name, 'upper_bound']
        
        # Convert low_bound and upper_bound to numeric types
        low_bound_numeric = pd.to_numeric(low_bound)
        upper_bound_numeric = pd.to_numeric(upper_bound)
        
        # Find the column name in the array
        start_index = np.where(array == column_name)[0]

        if len(start_index) == 0:
            print(f"Target string '{column_name}' not found in the array.")
            continue

        start_index = start_index[0]

        # Find the index of the next '####'
        end_index = np.where(array == '####')[0]

        if len(end_index) == 0:
            print("No '####' found after the target string.")
            continue

        end_index = end_index[np.where(end_index > start_index)]

        if len(end_index) == 0:
            print("No '####' found after the target string.")
            continue

        end_index = end_index[0]

        # Skip the first 5 lines for nmonths
        start_index += 6

        # Save the range between start and end index to a NumPy array
        result_array = np.arange(start_index, end_index + 1)

        # Iterate through rows in the DataFrame
        for row_index in dataframe.index:
            # Map row_index to the corresponding index in result_array
            index_to_update = (row_index - 1) * 12

            if index_to_update < 0 or index_to_update + 11 >= len(array):
                print(f"Index value '{row_index}' is out of range for '{column_name}'. Skipping.")
                continue

            # Convert the array values to numeric before performing multiplication
            array_values_numeric = pd.to_numeric(array[result_array[index_to_update:index_to_update + 12]])

            # Perform updates by multiplying the array value by the corresponding one in the DataFrame
            for i in range(12):
                updated_value = array_values_numeric[i] * dataframe.at[row_index, column_name]
                # Apply lower and upper bounds
                if updated_value > upper_bound_numeric:
                    updated_value = upper_bound_numeric
                elif updated_value < low_bound_numeric:
                    updated_value = low_bound_numeric
                array[result_array[index_to_update + i]] = updated_value

    return array

def remove_invalid_values(simulated, observed):
    valid_indices = np.where((observed != -9999) & (simulated != -9999))
    return simulated[valid_indices], observed[valid_indices]

def remove_nan_rows(
    array1: np.ndarray, 
    array2: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Removes rows from two arrays where either array has NaN values.
    Retains the first row if it doesn't have any NaN values.
    
    Arguments:
    array1: np.ndarray:
        First input array
    array2: np.ndarray
        Second input array
    
    Returns:
    cleaned_array1: : np.ndarray
        Cleaned array1 without NaN rows
    cleaned_array2: np.ndarray
        Cleaned array2 without NaN rows
    """
    # checks for and removes any rows where either array has a value of NaN at a corresponding row 
    # including the first one
    
    mask = np.logical_and(~np.isnan(array1), ~np.isnan(array2))
    if not np.isnan(array1[0]) and not np.isnan(array2[0]):
        mask[0] = True
    cleaned_array1 = array1[mask]
    cleaned_array2 = array2[mask]
    return cleaned_array1, cleaned_array2


def compute_kge(simulated_array, observed_array):
    """
    Computes KGE (Kling-Gupta Efficiency) between observed and simulated values.

    Parameters:
        observed_array (numpy.ndarray): Array of observed values.
        simulated_array (numpy.ndarray): Array of simulated values.

    Returns:
        float: KGE value.
    """
    
    # Calculate Pearson correlation coefficient
    correlation_coefficient = np.corrcoef(observed_array, simulated_array)[0, 1]
    
    # Calculate standard deviation ratio
    std_observed = np.std(observed_array)
    std_simulated = np.std(simulated_array)
    std_ratio = std_simulated / std_observed
    
    # Calculate bias ratio
    mean_observed = np.mean(observed_array)
    mean_simulated = np.mean(simulated_array)
    bias_ratio = mean_simulated / mean_observed
    
    # Calculate KGE
    kge = 1 - np.sqrt((correlation_coefficient - 1)**2 + (std_ratio - 1)**2 + (bias_ratio - 1)**2)
    return -kge

if __name__ == "__main__":
    print(os.getcwd())
    executable_directory = './data'

    # Change the current working directory to the specified directory
    os.chdir(executable_directory)
    monthly= pd.read_csv('./monthly.txt', sep=' ', index_col= 0)
    
    
    # In[9]:
    
    
    # Read Par File into a numpy array to convert to Paired    
    with open('./myparam.param', 'r') as file:
        lines = file.readlines()
    par = np.array([line.strip() for line in lines])
    
    
    # read ranges into a dataframe
    par_range= pd.read_csv('./nhm_monthly_range.txt', sep='\t', index_col= 0)
    
    
    # In[10]:
    
    
    updated_par= update_adj(par, monthly, par_range)
    
    
    # In[11]:
    
    
    # Save the parpaired to the specified file path
    np.savetxt('./myparam.param', updated_par, fmt='%s')
    
    
    # In[32]:
    
    
    # run prms
    subprocess.run(['./prms', '-C./control.default.bandit'])
    
    
    # In[13]:
    
    
    # Create an empty list to store total KGE values for each file
    total_kge_values  = []
    
    
    # In[14]:
    
    
    file_names = []
    
    
    # In[15]:
    
    
    year_ranges = [('1981-01-01', '1984-12-31'),
                   ('1990-01-01', '1998-12-31'),
                   ('2004-01-01', '2007-12-31'),
                   ('2013-01-01', '2015-12-31')]
    
    
    # Read statvar
    
    # In[16]:
    
    
    # Read space-separated file into DataFrame, skipping 28 rows
    simulated = pd.read_csv('./statvar.out', sep=' ', skiprows=29, header=None)
    
    
    # In[17]:
    
    
    # Drop the specified columns
    columns_to_drop = [0, 4, 5, 6, len(simulated.columns) - 1]  # 0-based index of columns to drop
    simulated = simulated.drop(columns=columns_to_drop, axis=1)
    
    
    # In[18]:
    
    
    # Combine the first 3 columns as datetime
    simulated['date'] = pd.to_datetime(simulated.iloc[:, :3].astype(str).agg('-'.join, axis=1))
    
    
    # In[19]:
    
    
    # Set the new 'date' column as the index
    simulated.set_index('date', inplace=True)
    
    
    # In[20]:
    
    
    # Drop the original three columns
    simulated = simulated.drop(simulated.columns[:3], axis=1)
    
    
    # In[21]:
    
    
    # Filter the DataFrame to keep only rows within the specified year ranges
    simulated_filtered = pd.concat([simulated.loc[start_date:end_date] for start_date, end_date in year_ranges])
    
    
    # Read infilled
    
    # In[22]:
    
    
    # Read space-separated file into DataFrame, skipping 28 rows
    infill = pd.read_csv('./infill_sf_data', sep=' ', skiprows=23, header=None)
    
    
    # In[23]:
    
    
    # Drop the specified columns
    columns_to_drop = [3, 4, 5]  # 0-based index of columns to drop
    infill = infill.drop(columns=columns_to_drop, axis=1)
    
    
    # In[24]:
    
    
    # Combine the first 3 columns as datetime
    infill['date'] = pd.to_datetime(infill.iloc[:, :3].astype(str).agg('-'.join, axis=1))
    
    
    # In[25]:
    
    
    # Set the new 'date' column as the index
    infill.set_index('date', inplace=True)
    
    
    # In[26]:
    
    
    # Drop the original three columns
    drop = [0, 1, 2]  # 0-based index of columns to drop
    infill = infill.drop(columns=drop, axis=1)
    
    
    # In[27]:
    
    
    # Filter the DataFrame to keep only rows within the specified year ranges
    infill_filtered = pd.concat([infill.loc[start_date:end_date] for start_date, end_date in year_ranges])
    
    
    # In[28]:
    
    
    # specify column index for matching dataframes
    column_index = 3

    # Extract the simulated and observed arrays
    simulated_array = simulated_filtered.iloc[:, column_index].values
    observed_array = infill_filtered.iloc[:, column_index].values

    # Remove invalid values (-9999) after concatenating arrays
    simulated_array, observed_array = remove_invalid_values(simulated_array, observed_array)

    # Check for and remove rows with nan
    simulated_array, observed_array = remove_nan_rows(simulated_array, observed_array)

    # Check if both arrays have the same length
    if len(observed_array) != len(simulated_array):
        raise ValueError("Observed and simulated data arrays have different lengths!")

    # Calculate KGE for the specified pair of columns
    total_kge = compute_kge(simulated_array, observed_array)

    # Save total KGE to the list
    total_kge_values.append(total_kge)
    
    # Calculate the average KGE
    average_kge = np.mean(total_kge_values)
 
    # Output the average KGE to a text file
    output_file_path = './average_kge.txt'
    with open(output_file_path, 'w') as file:
        file.write(str(average_kge))
