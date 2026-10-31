import argparse
import logging
import random
import sys

import pandas as pd
import yaml
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description="Randomly swaps values between specified columns/attributes in a dataset.")
    parser.add_argument("data_file", help="Path to the data file (e.g., CSV, Excel)")
    parser.add_argument("config_file", help="Path to the configuration file (YAML)")
    parser.add_argument("--output_file", "-o", help="Path to the output file. It must not resolve to the data file. A name ending in .xlsx or .xls is written as an Excel workbook, anything else as CSV.", default="masked_data.csv") #added output file argument
    parser.add_argument("--log_level", "-l", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", default="INFO") #added log level
    return parser

def validate_config(config):
    """
    Validates the configuration file.

    Args:
        config (dict): The configuration dictionary.

    Returns:
        bool: True if the configuration is valid, False otherwise.
    """
    if not isinstance(config, dict):
        logging.error("Configuration file must be a dictionary.")
        return False

    if "columns_to_swap" not in config:
        logging.error("Configuration file must contain 'columns_to_swap'.")
        return False

    columns_to_swap = config["columns_to_swap"]

    if not isinstance(columns_to_swap, list):
        logging.error("'columns_to_swap' must be a list.")
        return False

    if not columns_to_swap:
        logging.error("'columns_to_swap' must not be empty: a run with no pairs swaps nothing.")
        return False

    for swap_pair in columns_to_swap:
        if not isinstance(swap_pair, list) or len(swap_pair) != 2:
            logging.error("Each element in 'columns_to_swap' must be a list of two column names.")
            return False

    return True

def swap_data(df, columns_to_swap):
    """
    Randomly swaps data between specified columns in a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.
        columns_to_swap (list): A list of column pairs to swap.  Each pair should be a list of two column names.

    Returns:
        pd.DataFrame: The DataFrame with swapped data.
    """
    for col1, col2 in columns_to_swap:
        if col1 not in df.columns or col2 not in df.columns:
            # A pair naming a missing column must fail the run, not be
            # skipped while the tool reports completion on unswapped data.
            raise ValueError(f"Column(s) '{col1}' or '{col2}' not found in the DataFrame.")

        # The exchange is deliberately lopsided. col2 receives col1 in its
        # original row order, while col1 receives a permuted copy of col2,
        # so neither column keeps its old row pairing with the other. A
        # plain per-row swap would preserve those pairings exactly.
        # The staging name is lengthened until it cannot collide with a
        # real column; overwriting and then dropping a user's own
        # temp_<col2> column would silently delete their data.
        temp_col = f"temp_{col2}"
        while temp_col in df.columns:
            temp_col = "_" + temp_col
        df[temp_col] = df[col2].sample(frac=1, random_state=random.randint(0, 1000)).reset_index(drop=True)

        df[col2] = df[col1].copy()  # Copy values from col1 to col2
        df[col1] = df[temp_col].copy() # Copy values from temp to col1

        # Remove the temporary column
        df.drop(columns=[temp_col], inplace=True)

        logging.info(f"Swapped data between columns '{col1}' and '{col2}'.")

    return df


def main():
    """
    Main function to execute the data attribute swapper tool.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Set logging level
    try:
        logging.getLogger().setLevel(args.log_level.upper())
    except ValueError:
        logging.error(f"Invalid log level: {args.log_level}.  Using INFO instead.")
        logging.getLogger().setLevel(logging.INFO)

    logging.info("Starting dm-data-attribute-swapper")

    if Path(args.data_file).resolve() == Path(args.output_file).resolve():
        logging.error("Error: Output file cannot be the same file as the data file.")
        sys.exit(1)

    try:
        # Load configuration file
        with open(args.config_file, 'r') as f:
            config = yaml.safe_load(f)

        if not validate_config(config):
            logging.error("Invalid configuration file. Exiting.")
            sys.exit(1)

        # Load data file
        file_extension = os.path.splitext(args.data_file)[1].lower()
        if file_extension == ".csv":
            df = pd.read_csv(args.data_file)
        elif file_extension == ".xlsx" or file_extension == ".xls":
            df = pd.read_excel(args.data_file)
        else:
            logging.error("Unsupported file format. Only CSV and Excel files are supported.")
            sys.exit(1)

        logging.info(f"Loaded data from '{args.data_file}' with shape: {df.shape}")

        # Swap data based on configuration
        df = swap_data(df, config["columns_to_swap"])

        # Save the masked data to a new file. An Excel named output gets a
        # real Excel workbook; anything else gets CSV. If no Excel engine
        # is available for the named format, refuse instead of writing CSV
        # bytes under an Excel name.
        output_extension = os.path.splitext(args.output_file)[1].lower()
        if output_extension in (".xlsx", ".xls"):
            try:
                df.to_excel(args.output_file, index=False)
            except Exception as e:
                if isinstance(e, ImportError) or "No engine" in str(e):
                    logging.error(
                        f"No Excel engine is available to write '{args.output_file}'. "
                        "Refusing to write CSV data under an Excel file name."
                    )
                    sys.exit(1)
                raise
        else:
            df.to_csv(args.output_file, index=False)
        logging.info(f"Masked data saved to '{args.output_file}'")

    # Every failure path exits 1. These branches used to fall through to
    # the completion log line below, so a missing file or a bad config
    # reported success to any script driving this tool.
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logging.error(f"The data file '{args.data_file}' is empty.")
        sys.exit(1)
    except SystemExit:
        raise
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.exception("Detailed error information:")  # Include traceback
        sys.exit(1)

    logging.info("dm-data-attribute-swapper completed.")


if __name__ == "__main__":
    main()