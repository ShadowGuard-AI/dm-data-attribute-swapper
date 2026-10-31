![Banner](banner.png)

# dm-data-attribute-swapper
Randomly swaps values between specified columns or attributes within a dataset. The tool takes a configuration file specifying the columns to swap, and a data source file. This is useful for disrupting correlations between attributes. - Focused on Tools designed to generate or mask sensitive data with realistic-looking but meaningless values

## Install
`git clone https://github.com/ShadowStrikeHQ/dm-data-attribute-swapper`

## Usage
`./dm-data-attribute-swapper [params]`

## Parameters
- `-h`: Show help message and exit
- `data_file`: Path to the data file (CSV or Excel)
- `config_file`: Path to the YAML configuration file naming the column pairs in `columns_to_swap`
- `--output_file`: Path to the output file. It must not be the data file: if the output path resolves to the data file, the run refuses and exits 1 before any write. A name ending in .xlsx or .xls is written as a real Excel workbook when an engine for that format is available, and the run refuses at exit 1 when none is available, rather than writing CSV bytes under an Excel name. Any other name is written as CSV.
- `--log_level`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Failure rules
- If any configured pair names a column that is not in the data, the run exits 1 and writes no output.
- An empty `columns_to_swap` list is rejected as an invalid configuration: the run exits 1 and writes no output.

## License
Copyright (c) ShadowStrikeHQ
