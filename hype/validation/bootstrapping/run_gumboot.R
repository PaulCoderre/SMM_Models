# Set CRAN mirror to avoid errors when loading packages
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Load necessary libraries
# install.packages("gumboot")

library(gumboot)
library(dplyr) 
library(ggplot2)
library(reshape2)  

# Set the working directory to getwd() + "./working_directory"
setwd(getwd())

# Read the gauge_key DataFrame from a CSV file
gauge_key <- read.csv("../../SMM_Models/hype/geospacial/misc/hype_naturalized_flows_summary.csv")

# List all CSV files in the working directory
files <- list.files(pattern = "^00.*\\.csv$") 

# Initialize empty lists to store bootjack results
bootjack_results <- list()

# Process each CSV file
for (file in files) {
  # Read the CSV file into a DataFrame
  flows <- read.csv(file)
  
  # Convert the date column to Date type
  flows$date <- as.Date(flows$date)
  
  # Ensure obs and sim columns are numeric
  flows$obs <- as.numeric(flows$obs)
  flows$sim <- as.numeric(flows$sim)
  
  # Check the structure of the data (optional)
  print(head(flows))
  print(str(flows))
  
  # Calculate bootjack values for NSE and KGE
  bootjack_nse_values <- bootjack(flows, GOF_stat = "NSE", returnSamples = TRUE)
  bootjack_kge_values <- bootjack(flows, GOF_stat = "KGE", returnSamples = TRUE)
  bootjack_stats <- bootjack(flows) # for summary table
  
  # Get the length of the DataFrame (number of rows)
  df_length <- nrow(flows)
  
  # Append length to the bootjack_stats DataFrame
  bootjack_stats$Length <- df_length
  
  # Drop '00' prefix and '.csv' suffix from the filename
  file_base <- sub("^00", "", sub("\\.csv$", "", file))
  
  # Find the corresponding subbasin_id in gauge_key
  subbasin_id <- gauge_key$subbasin_id[gauge_key$subbasin_id == file_base]
  
  # If subbasin_id is found, get the real_stream_name
  if (length(subbasin_id) > 0) {
    real_stream_name <- gauge_key$real_stream_name[gauge_key$subbasin_id == subbasin_id]
    
    # Append real_stream_name to the bootjack_stats DataFrame
    bootjack_stats$real_stream_name <- real_stream_name
    
    # Store the bootjack_stats with updated information
    bootjack_results[[file]] <- bootjack_stats
    
    # Create a histogram plot of the bootstrap samples for NSE
    p_nse <- ggplot(bootjack_nse_values$statsBoot, aes(NSE)) + 
      geom_histogram(binwidth = 0.01, fill = "blue", color = "black", alpha = 0.7) +
      ggtitle(paste("Bootstrap Samples for NSE -", real_stream_name)) +  # Use real_stream_name for title
      xlab("NSE") +
      ylab("Frequency")
    
    # Save the plot for NSE to a file
    plot_file_name_nse <- paste0("histogram_NSE_", gsub(" ", "_", real_stream_name), ".png") # Save as PNG
    ggsave(plot_file_name_nse, plot = p_nse, width = 8, height = 5)  # Adjust width and height as needed
    
    # Create a histogram plot of the bootstrap samples for KGE
    p_kge <- ggplot(bootjack_kge_values$statsBoot, aes(KGE)) + 
      geom_histogram(binwidth = 0.01, fill = "green", color = "black", alpha = 0.7) +
      ggtitle(paste("Bootstrap Samples for KGE -", real_stream_name)) +  # Use real_stream_name for title
      xlab("KGE") +
      ylab("Frequency")
    
    # Save the plot for KGE to a file
    plot_file_name_kge <- paste0("histogram_KGE_", gsub(" ", "_", real_stream_name), ".png") # Save as PNG
    ggsave(plot_file_name_kge, plot = p_kge, width = 8, height = 5)  # Adjust width and height as needed
  } else {
    warning(paste("Subbasin ID not found for file:", file))
  }
}

# Convert the list of results to a DataFrame
bootjack_results_df <- do.call(rbind, bootjack_results)

# Save the resulting DataFrame to a CSV file
write.csv(bootjack_results_df, file = "bootjack_results.csv", row.names = TRUE)

# Optional: Print a message indicating that the script has finished running
print("Bootjack results have been saved to bootjack_results.csv.")

# Create separate dataframes for NSE and KGE results
bootjack_nse_results <- bootjack_results_df[bootjack_results_df$GOF_stat == "NSE", ]
bootjack_kge_results <- bootjack_results_df[bootjack_results_df$GOF_stat == "KGE", ]



# Function to create seJab vs real_stream_name plots
create_seJab_plot <- function(data, color, title, file_name) {
  p <- ggplot(data, aes(x = real_stream_name, y = seJab)) +
    geom_point(color = color) +
    geom_line() +  # Optional: add lines connecting points
    ggtitle(title) +
    xlab("Real Stream Name") +
    ylab("seJab") +
    theme(axis.text.x = element_text(angle = 70, hjust = 1))
  
  # Save the plot to a file
  ggsave(file_name, plot = p, width = 10, height = 6)
}

# Call the function for NSE results
create_seJab_plot(bootjack_nse_results, "blue", "Standard Error Jacknife After Bootstrap vs Real Stream Name (NSE Results)", "seJab_vs_real_stream_name_nse.png")

# Call the function for KGE results
create_seJab_plot(bootjack_kge_results, "red", "Standard Error Jacknife After Bootstrap vs Real Stream Name (KGE Results)", "seJab_vs_real_stream_name_kge.png")



# Function to create plots for given results
create_percentile_plot <- function(data, metric, file_suffix) {
  # Reshape data for plotting
  melted_data <- melt(data, id.vars = "real_stream_name", measure.vars = c("p05", "p50", "p95"))
  
  # Create plot
  p <- ggplot(melted_data, aes(x = real_stream_name, y = value, color = variable)) +
    geom_point() +
    geom_line(aes(group = variable)) +  # Connect points for each percentile
    ggtitle(paste("Percentiles vs Real Stream Name (", metric, " Results)", sep = "")) +
    xlab("Real Stream Name") +
    ylab("Value") +
    scale_color_manual(values = c("p05" = "blue", "p50" = "green", "p95" = "red")) +
    theme(axis.text.x = element_text(angle = 70, hjust = 1))
  
  # Save the plot to a file
  ggsave(paste("percentiles_vs_real_stream_name_", file_suffix, ".png", sep = ""), plot = p, width = 10, height = 6)
}
# Create plots for NSE results
create_percentile_plot(bootjack_nse_results, "NSE", "nse")

# Create plots for KGE results
create_percentile_plot(bootjack_kge_results, "KGE", "kge")

