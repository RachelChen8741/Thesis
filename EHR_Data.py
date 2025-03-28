import pandas as pd

# Load your data
file_path = '/Users/rachelchen/Desktop/Thesis/ehrshot.csv'
data = pd.read_csv(file_path, low_memory=False)
data = data.drop(columns=['omop_table'])

# Specify the new file path where you want to save the updated CSV
output_file_path = '/Users/rachelchen/Desktop/EHRSHOT_ASSETS/data/ehrshot_updated.csv'

# Save the DataFrame to the new CSV file
data.to_csv(output_file_path, index=False)
