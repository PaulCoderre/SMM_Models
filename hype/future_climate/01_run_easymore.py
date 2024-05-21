from easymore import Easymore
import os
import sys

esmr = Easymore()

# Access the environment variable set by the shell script
# directory_index = os.getenv("SLURM_ARRAY_TASK_ID")
if len(sys.argv) != 2:
    print("Usage: python run_easymore.py <index>")
    sys.exit(1)

directory_index = int(sys.argv[1])
print(directory_index)

# convert directory index to int
directory_index = int(directory_index)

directory_index_str = str(directory_index)
if len(directory_index_str) == 1:
    directory_index_str = "0" + directory_index_str

# Open the file in read mode
with open("/home/paulc600/scratch/directories.txt", "r") as file:
    # Read the lines of the file and remove any trailing whitespace
    directory = [line.strip() for line in file.readlines()]

esmr.case_name                = f'{directory_index_str}_hype_smm_cmip'

esmr.temp_dir                 = f'/home/paulc600/scratch/temp/{directory_index_str}_temp_dir/'

esmr.target_shp               = '/home/paulc600/local/smm_final/StMaryMilk2023-UofC/models/hype/geospacial/shapefiles/modified_shapefiles/Modified_SMMcat.shp'

esmr.target_shp_ID            = 'seg_nhm'

esmr.source_nc                = f'{directory[directory_index]}/*.nc'

esmr.var_names                = ['pr','tasmax','tasmin']

esmr.var_names_remapped       = ['precipitation','max_temperature','min_temperature']

esmr.var_lon                  = 'lon'

esmr.var_lat                  = 'lat'

esmr.var_time                 = 'time'

esmr.output_dir               = f'/home/paulc600/scratch/easymore_results/{directory_index_str}_easymore_cmip/'

# Create the directory
os.makedirs(esmr.output_dir, exist_ok=True)

# Check if directory was created
if os.path.exists(esmr.output_dir ):
    print(f"Directory '{esmr.output_dir }' created successfully!")
else:
    print(f"Failed to create directory '{esmr.output_dir }'!")

esmr.format_list              = ['f4']

esmr.fill_value_list          = ['-9999.00']

esmr.save_csv                 = True

esmr.complevel                = 9

esmr.nc_remapper()
