"""
Unit tests for the OnyxAnalysis class and associated functions. To save
generated test results in the repo, run the following command from the
top folder:
pytest tests/test_onyx_analysis_helper.py -rP --basetemp tests/test_outputs/

WARNING: Using --basetemp on an existing folder will overwrite all files.
"""

import os
import pytest
import importlib.metadata as metadata
import regex as re

from onyx_analysis_helper import onyx_analysis_helper_functions as oa
from onyx import OnyxConfig, OnyxEnv
from onyx.exceptions import (
    OnyxError,
    OnyxConnectionError,
    OnyxConfigError,
    OnyxClientError,
    OnyxHTTPError
)

# Fixtures
@pytest.fixture
def example_methods():
    methods_dict = {"method1": "method example 1",
                    "method2": "method example 2"}

    return methods_dict

@pytest.fixture
def expected_methods_json():
    methods_json = '{"method1": "method example 1", "method2": "method example 2"}'

    return methods_json

@pytest.fixture
def example_results():
    methods_dict = {"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}

    return methods_dict

@pytest.fixture
def expected_results():
    methods_json = '{"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}'

    return methods_json

@pytest.fixture
def onyx_json_file_path(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("onyx_analysis_tests") / "onyx_analysis.json"
    return str(tmp_dir)

@pytest.fixture
def complete_field_dict():
    field_dict = {"name": "test-analysis", "description": "This is a test analysis",
                  "analysis_date": "2025-08-21", "pipeline_name": "test-pipeline",
                  "pipeline_url": "test-pipeline-url", "pipeline_version": "0.1.0",
                  "result": "test result", "upstream_analyses": [], "report": "",
                  "outputs": "path/to/outputs",
                  "methods": '{"method1": "method example 1", "method2": "method example 2"}',
                  "result_metrics": '{"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}',
                  "synthscape_records": ["C-123456789"], "identifiers": []}

    return field_dict

@pytest.fixture
def missing_field_dict():
    field_dict = {"description": "This is a test analysis",
                  "analysis_date": "2025-08-21", "pipeline_name": "test-pipeline",
                  "pipeline_url": "test-pipeline-url", "pipeline_version": "0.1.0",
                  "result": "test result", "upstream_analyses": [], "report": "",
                  "outputs": "path/to/outputs",
                  "methods": '{"method1": "method example 1", "method2": "method example 2"}',
                  "result_metrics": '{"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}',
                  "synthscape_records": ["C-123456789"], "identifiers": []}

    return field_dict

@pytest.fixture
def missing_field_log():
    logs = ["Missing required fields: ['name']"]
    return logs

@pytest.fixture
def missing_output_dict():
    field_dict = {"name": "test-analysis", "description": "This is a test analysis",
                  "analysis_date": "2025-08-21", "pipeline_name": "test-pipeline",
                  "pipeline_url": "test-pipeline-url", "pipeline_version": "0.1.0",
                  "result": "test result", "upstream_analyses": [],
                  "methods": '{"method1": "method example 1", "method2": "method example 2"}',
                  "result_metrics": '{"Example result 1": 9, "Example result 2": "Fail", "Example result 3": 0.3}',
                  "synthscape_records": ["C-123456789"], "identifiers": []}

    return field_dict

@pytest.fixture
def missing_output_log():
    logs = ["Fields dict must contain one of: ['report', 'outputs']"]
    return logs

@pytest.fixture
def missing_both_dict():
    field_dict = {"description": "This is a test analysis",
                  "analysis_date": "2025-08-21", "pipeline_name": "test-pipeline",
                  "pipeline_url": "test-pipeline-url", "pipeline_version": "0.1.0",
                  "result": "test result", "upstream_analyses": [],
                  "methods": '{"method1": "method example 1", "method2": "method example 2"}',
                  "result_metrics": '{"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}',
                  "synthscape_records": ["C-123456789"], "identifiers": []}

    return field_dict

@pytest.fixture
def missing_both_log():
    logs = ["Missing required fields: ['name']",
            "Fields dict must contain one of: ['report', 'outputs']"]
    return logs

@pytest.fixture
def example_onyx_json_file():
    file = "tests/test_data/example_onyx_analysis.json"

    return file

@pytest.fixture
def example_onyx_json_file_fail():
    file = "tests/test_data/example_onyx_analysis_fail.json"

    return file

@pytest.fixture
def invalid_field_dict():
    field_dict = {"invalid_name": "test-analysis", "description": "This is a test analysis",
                  "analysis_date": "2025-08-21", "pipeline_name": "test-pipeline",
                  "pipeline_url": "test-pipeline-url", "pipeline_version": "0.1.0",
                  "result": "test result", "upstream_analyses": [], "report": "",
                  "outputs": "path/to/outputs",
                  "methods": '{"method1": "method example 1", "method2": "method example 2"}',
                  "result_metrics": '{"Example result 1": 9, "Example reuslt 2": "Fail", "Example result 3": 0.3}',
                  "synthscape_records": ["C-123456789"], "identifiers": []}

    return field_dict

# Tests
def test_add_analysis_details():
    expected_name = "example_analysis"
    expected_description = "This is an example analysis."
    analysis = oa.OnyxAnalysis()
    analysis.add_analysis_details(expected_name, expected_description)

    assert analysis.name == expected_name
    assert analysis.description == expected_description

def test_add_package_metadata():
    analysis = oa.OnyxAnalysis()
    analysis.add_package_metadata("climb-onyx-client")
    version_check = re.fullmatch("[0-9]+\\.[0-9]+\\.[0-9]+", analysis.version)

    assert analysis.pipeline_name == "climb-onyx-client"
    assert analysis.description ==  "CLI and Python library for Onyx"
    assert version_check != None
    assert analysis.pipeline_url == "https://github.com/CLIMB-TRE/onyx-client"

def test_add_methods(example_methods, expected_methods_json):
    analysis = oa.OnyxAnalysis()
    analysis.add_methods(example_methods)

    assert analysis.methods == expected_methods_json

def test_add_results(example_results, expected_results):
    result = "headline result"
    analysis = oa.OnyxAnalysis()
    analysis.add_results(result, example_results)

    assert analysis.result == result
    assert analysis.result_metrics == expected_results

def test_add_server_records():
    sample_id = "C-123456789"
    server = "synthscape"
    analysis = oa.OnyxAnalysis()
    analysis.add_server_records(sample_id, server)

    assert analysis.synthscape_records == "C-123456789"

@pytest.mark.skip
def test_write_analysis_to_onyx():
    result == {}
    expected_result == {}
    assert result == expected_result

def test_write_analysis_to_json(onyx_json_file_path, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    for key, value in complete_field_dict.items():
            setattr(analysis, key, value)
    analysis.write_analysis_to_json(onyx_json_file_path)

    assert os.path.exists(onyx_json_file_path)

def test_check_required_fields_passes(complete_field_dict, caplog):
    analysis = oa.OnyxAnalysis()
    analysis._check_required_fields(complete_field_dict)

    assert caplog.text == ""

@pytest.mark.parametrize("test_input,log_message", [("missing_field_dict", "missing_field_log"),
                                                    ("missing_output_dict", "missing_output_log"),
                                                    ("missing_both_dict", "missing_both_log")])
def test_check_required_fields_fails(test_input, log_message, request, caplog):
    fields_dict = request.getfixturevalue(test_input)
    log_message = request.getfixturevalue(log_message)

    analysis = oa.OnyxAnalysis()
    analysis._check_required_fields(fields_dict)

    assert all(messages in caplog.text for messages in log_message)

def test_read_analysis_from_json_pass(example_onyx_json_file, complete_field_dict):
    analysis = oa.OnyxAnalysis()
    analysis.read_analysis_from_json(example_onyx_json_file)
    assert analysis.__dict__ == complete_field_dict

def test_read_analysis_from_json_fail(example_onyx_json_file_fail, complete_field_dict, caplog):
    analysis = oa.OnyxAnalysis()
    analysis.read_analysis_from_json(example_onyx_json_file_fail)
    message = "Invalid attribute in onyx analysis: ['invalid_field']"

    assert message in caplog.text

def test_set_attributes_pass(complete_field_dict):
    analysis = oa.OnyxAnalysis()
    analysis._set_attributes(complete_field_dict)

    assert analysis.__dict__ == complete_field_dict

def test_set_attributes_fail(invalid_field_dict, complete_field_dict, caplog):
    analysis = oa.OnyxAnalysis()
    analysis._set_attributes(invalid_field_dict)

    message = "Invalid attribute in onyx analysis: ['invalid_name']"

    assert message in caplog.text
