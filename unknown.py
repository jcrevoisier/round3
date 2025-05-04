import csv

input_file = 'round_2_10000_facilities.csv'
output_file = 'unknown_beds_facilities.csv'

with open(input_file, 'r', newline='', encoding='utf-8') as infile, \
     open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    # Read header and write it to output file
    header = next(reader)
    writer.writerow(header)
    
    # Process each row
    for row in reader:
        # Check if "Number of beds estimated" column contains "Unknown"
        print(row[5])
        if len(row) >= 6 and row[5] == "Unknown":
            writer.writerow(row)

print(f"Extraction complete. Rows with unknown bed counts saved to {output_file}")
