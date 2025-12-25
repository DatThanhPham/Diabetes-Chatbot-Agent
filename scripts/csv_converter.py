import pandas as pd
import sys
from pathlib import Path

def convert_xpt_to_csv(xpt_file, csv_file=None):
    """
    Convert an XPT file to CSV format.
    
    Args:
        xpt_file (str): Path to the input XPT file
        csv_file (str, optional): Path to the output CSV file. 
                                   If not provided, uses the same name as input with .csv extension
    """
    try:
        # Convert string paths to Path objects
        xpt_path = Path(xpt_file)
        
        # Validate input file exists
        if not xpt_path.exists():
            print(f"Error: File '{xpt_file}' not found.")
            return False
        
        # Determine output file path
        if csv_file is None:
            csv_path = xpt_path.with_suffix('.csv')
        else:
            csv_path = Path(csv_file)
        
        print(f"Reading XPT file: {xpt_path}")
        
        # Read XPT file (SAS format)
        df = pd.read_sas(xpt_path)
        
        print(f"Successfully read {len(df)} rows and {len(df.columns)} columns")
        
        # Write to CSV
        df.to_csv(csv_path, index=False)
        
        print(f"Successfully converted to CSV: {csv_path}")
        return True
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <input_xpt_file> [output_csv_file]")
        print("Example: python script.py data.xpt")
        print("Example: python script.py data.xpt output.csv")
        sys.exit(1)
    
    xpt_input = sys.argv[1]
    csv_output = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = convert_xpt_to_csv(xpt_input, csv_output)
    sys.exit(0 if success else 1)