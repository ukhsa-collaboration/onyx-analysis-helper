# onyx-analysis-helper

This repository contains helper functions that can be used to format
analyses ready for submission to onyx.

## Installation as standalone code

Clone repo and create environment:
`git clone git@github.com:ukhsa-collaboration/onyx-analysis-helper.git`

`conda env create -n mscape_analysis`

`conda activate mscape_analysis`

Installation for users:
`cd onyx-analysis-helper`
`pip install .`

Installation for developers (installs code in editable mode):
`cd mscape-template`
`pip install --editable '.[dev]'`

## Installation in another project

To install the codebase as part of another project, add this to your pyproject.toml
under [project] dependencies:
`
[project]
dependencies = ["climb-onyx-client", "onyx-analysis-helper@git+https://github.com/ukhsa-collaboration/onyx-analysis-helper.git"]
`

## Usage

Functionality from the repo can be imported into other code after
installation:
```python
from onyx_analysis_helper import onyx_analysis_helper_functions as oa
```

Example usage to instantiate an OnyxAnalysis object, add required information, and
check all fields are present and correct:
```python
# Instantiate the class
onyx_analysis = oa.OnyxAnalysis()

# Add details on the analysis
onyx_analysis.add_analysis_details(
    analysis_name="example-analysis",
    analysis_description="""This is an analysis to generate example statistics for samples"""
    )

# Add package metadata - takes from package name if code base is pip installed
onyx_analysis.add_package_metadata(package_name = "package-name-here")

# Add methods information e.g. QC thresholds used. Must be in dictionary format
methods_fail = onyx_analysis.add_methods(methods_dict = example_thresholds)

# Add results information e.g. QC results. Must be in dictionary format. More detailed
# results to be added in output files/report.
results_fail = onyx_analysis.add_results(top_result = headline_result, results_dict = example_results)

# Add climb ID - field is either mscape_records or synthscape_records
onyx_analysis.add_server_records(sample_id = record_id, server_name = "synthscape")

# Add location of output files. Add report field is single file provided, add outputs field
# if results directory is provdied.
output_fail = onyx_analysis.add_output_location(result_file)

# Checks all required fields are present and that there are no invalid fields
required_field_fail, attribute_fail = onyx_analysis.check_analysis_object()

# Check the fail statuses above and action as appropriate e.g. logging,
#exit code, raise an error etc:
if any([methods_fail, results_fail, output_fail, required_field_fail, attribute_fail]):
    "Incorrect attribute in analysis object, check logs for details"
else:
    "Correct attributes in analysis object"
```
