import csv
import random

input_file = 'unknown_beds_facilities.csv'
output_file = 'unknown_beds_100_facilities.csv'

# Read all rows from the input file
with open(input_file, 'r', newline='', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    header = next(reader)  # Get the header row
    rows = list(reader)    # Read all data rows

# Select 100 random rows (or all if less than 100)
sample_size = min(100, len(rows))
selected_rows = random.sample(rows, sample_size)

# Write the selected rows to the output file
with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile)
    writer.writerow(header)  # Write the header
    writer.writerows(selected_rows)  # Write the selected rows

print(f"Extraction complete. {sample_size} random rows saved to {output_file}")
