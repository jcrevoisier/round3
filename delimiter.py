import csv
import sys

def convert_delimiter(input_file, output_file):
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as infile:
            # Read the CSV with semicolon delimiter
            reader = csv.reader(infile, delimiter=';')
            
            # Store all rows
            rows = list(reader)
            
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            # Write the CSV with comma delimiter
            writer = csv.writer(outfile, delimiter=',')
            writer.writerows(rows)
            
        print(f"Successfully converted {input_file} to {output_file} with comma delimiter")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_csv_delimiter.py input.csv output.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    convert_delimiter(input_file, output_file)
