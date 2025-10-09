#!/usr/bin/env python3

"""
Module containing OnyxAnalysis class object and associated functions
to support submission and reading of onyx analyses.
"""

# Imports - ordered (can use ruff to do this automatically)
import datetime
import importlib.metadata as metadata
import json
import logging
import os
import time
from functools import wraps
from pathlib import Path

from onyx import OnyxClient, OnyxConfig, OnyxEnv
from onyx.exceptions import OnyxClientError, OnyxConfigError, OnyxConnectionError, OnyxHTTPError

# Set up e.g. config settings
# Set up onyx config
CONFIG = OnyxConfig(
    domain=os.environ[OnyxEnv.DOMAIN],
    token=os.environ[OnyxEnv.TOKEN],
)


# Onyx query decorator
def call_to_onyx(func):
    """Decorator that provides error handling and submission attempt
    functionality for any calls to Onyx.
    """

    @wraps(func)
    def call_to_onyx_wrapper(*args, **kwargs):
        connection_attempts = 1
        success = False

        while success is False:
            try:
                logging.debug(
                    "Attempting connection to Onyx. Attempt number %s", connection_attempts
                )
                result, exitcode = func(*args, **kwargs)
                success = True
                logging.debug("Successful connection to onyx")

                return result, exitcode

            except OnyxConnectionError as exc:
                if connection_attempts < 3:
                    connection_attempts += 1
                    logging.debug("OnyxConnectionError: %s. Retrying connection in 5 seconds", exc)
                    time.sleep(5)

                else:
                    logging.error(
                        """OnyxConnectionError: %s. Connection to Onyx failed %s times,
                              exiting program""",
                        exc,
                        connection_attempts,
                    )
                    result = None
                    exitcode = 1
                    return result, exitcode

            except OnyxConfigError as exc:
                logging.error(
                    """OnyxConfigError: %s. Check credentials and details in OnyxConfig
                          are correct. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details.""",
                    exc,
                )
                result = None
                exitcode = 1
                return result, exitcode

            except OnyxClientError as exc:
                logging.error(
                    """OnyxClientError: %s. Check calls to OnyxClient are correct
                          and required arguments e.g. climb_id are present. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details""",
                    exc,
                )
                result = None
                exitcode = 1
                return result, exitcode

            except OnyxHTTPError as exc:
                logging.error(
                    """OnyxHTTPError: %s. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details""",
                    exc.response.json(),
                )
                result = None
                exitcode = 1
                return result, exitcode

            except Exception as exc:
                logging.error(
                    """Unhandled error: %s. See
                          https://climb-tre.github.io/onyx-client/api/documentation/exceptions/
                          for more details""",
                    exc,
                )
                result = None
                exitcode = 1
                return result, exitcode

    return call_to_onyx_wrapper


# Functions


class OnyxAnalysis:
    def __init__(self):
        self.analysis_date: datetime.datetime
        self.name: str
        self.description: str
        self.pipeline_name: str
        self.pipeline_url: str
        self.pipeline_version: str
        self.pipeline_command: str | None
        self.methods: dict
        self.result: str
        self.result_metrics: dict
        self.report: os.path | None
        self.outputs: os.path | None
        self.upstream_analyses: str | None
        self.downstream_analyses: str | None
        self.identifiers: list[str] = []


    def add_analysis_details(self, analysis_name: str, analysis_description: str) -> None:
        """Adds analysis details to onyx analysis object. Sets analysis date
        if not already specified.
        """
        self.name = analysis_name
        self.description = analysis_description
        self._set_analysis_date()


    def add_package_metadata(self, package_name: str) -> None:
        "Adds package metadata to onyx analysis object"
        package_metadata = dict(metadata.metadata(package_name))
        self.pipeline_name = package_metadata["Name"]
        self.pipeline_version = package_metadata["Version"]
        self.pipeline_url = package_metadata["Project-URL"].split(", ")[
            1
        ]  # Get url from toml - add to template


    def add_methods(self, methods_dict: dict) -> bool:
        """Attempts to add methods to onyx analysis object. If results are
        invalid, returns results_fail.
        """
        if isinstance(methods_dict, dict):
            self.methods = json.dumps(methods_dict)
            methods_fail = False
        else:
            logging.error("Error: Methods must be in dict format")
            methods_fail = True

        return methods_fail


    def add_results(self, top_result: str, results_dict: dict) -> bool:
        """Attempts to add results to analysis object. If results are
        invalid, returns results_fail.
        """
        if isinstance(results_dict, dict):
            self.result = top_result
            self.result_metrics = json.dumps(results_dict)
            results_fail = False
        else:
            logging.error("Error: result_metrics must be in dict format")
            results_fail = True

        return results_fail


    def add_server_records(self, sample_id: str, server_name: str) -> None:
        """Creates records field for appropriate server e.g. "mscape_records"
        and adds sample_id to this field.
        """
        server_records = f"{server_name}_records"
        setattr(self, server_records, [sample_id])


    # Private methods for creating new analysis object
    def _set_analysis_date(self):
        self.analysis_date = datetime.datetime.now().date().isoformat()


    # Add in function to set s3 output path, other optional fields
    # Create analysis in Onyx
    @call_to_onyx
    def write_analysis_to_onyx(self, server: str, dryrun: bool) -> tuple[str,int]:
        """Attempts to add onyx analysis to object.
           Arguments:
               server -- Server submitting data to
               dryrun -- Specify if test or real upload to onyx
           Returns:
               result -- Analysis ID if valid submission, {} if test upload,
                         None if upload fails
               exitcode -- 0 if successful, 1 if fail
        """

        with OnyxClient(CONFIG) as client:
            result = client.create_analysis(project=server, fields=vars(self), test=dryrun)
        exitcode = 0

        return exitcode, result


    # Write analysis object to json
    def write_analysis_to_json(self, result_file: os.path) -> None:
        "Writes onyx analysis object to json"
        fields_dict = vars(self)
        self._check_required_fields(fields_dict)

        with Path(result_file).open("w") as file:
            json.dump(fields_dict, file)

    # Check fields
    @staticmethod
    def _check_required_fields(fields_dict):
        try:
            # Check required fields
            missing_field = False
            required_fields = [
                "analysis_date",
                "name",
                "pipeline_name",
                "pipeline_version",
                "result",
                "identifiers",
            ]
            if not all(field in fields_dict for field in required_fields):
                missing_fields = [field for field in required_fields if field not in fields_dict]
                logging.error("Missing required fields: %s", missing_fields)
                missing_field = True

            # Check outputs
            output_fields = ["report", "outputs"]
            if not any(field in output_fields for field in fields_dict):
                logging.error("Fields dict must contain one of: %s", output_fields)
                missing_field = True
            if missing_field:
                raise ValueError

        except ValueError as exc:
            return exc

    # Read in analysis information from json
    def read_analysis_from_json(self, analysis_json):
        with Path(analysis_json).open("r") as file:
            data = json.load(file)
        self._set_attributes(data)

    # Methods to read in existing analysis from onyx
    def read_analysis_from_onyx(self, analysis_id, project):
        analysis_dict = self._get_analysis_from_onyx(analysis_id, project)
        self._set_attributes(analysis_dict)

    @staticmethod
    @call_to_onyx
    def _get_analysis_from_onyx(analysis_id, project):
        with OnyxClient(CONFIG) as client:
            analysis_dict = client.get_analysis(project, analysis_id)
        return analysis_dict

    def _set_attributes(self, analysis_dict):
        valid_attributes = [
            "published_date",
            "site",
            "analysis_id",
            "analysis_date",
            "name",
            "description",
            "pipeline_name",
            "pipeline_url",
            "pipeline_version",
            "pipeline_command",
            "methods",
            "result",
            "result_metrics",
            "report",
            "outputs",
            "upstream_analyses",
            "downstream_analyses",
            "identifiers",
            "synthscape_records",
            "mscape_records",
        ]
        invalid_attributes = []

        for key, value in analysis_dict.items():
            if key in valid_attributes:
                setattr(self, key, value)
            else:
                invalid_attributes.append(key)

        if invalid_attributes != []:
            logging.error("Invalid attribute in onyx analysis: %s", invalid_attributes)
            attribute_fail = True

        return attribute_fail


    # Read in analysis information from json
    def read_analysis_from_json(self, analysis_json: os.path) -> None:
        "Reads analysis object from json and sets class attributes"
        with Path(analysis_json).open("r") as file:
            data = json.load(file)

        self._set_analysis_attributes(data)


    # Read in existing analysis from onyx
    def read_analysis_from_onyx(self, analysis_id: str, server: str) -> tuple[dict,int]:
        """Method to retrieve an analysis from Onyx and set class attributes from this.

           Arguments:
           analysis_id -- Name of analysis to be returned
           server -- Name of server to retrieve analysis from

        """
        analysis_dict, exitcode = self._get_analysis_from_onyx(analysis_id, server)
        if exitcode != 0:
            return analysis_dict, exitcode
        self._set_analysis_attributes(analysis_dict)

        return analysis_dict, exitcode


    @staticmethod
    @call_to_onyx
    def _get_analysis_from_onyx(analysis_id: str, server: str) -> tuple[dict,int]:
        "Retrieves analysis from Onyx"
        with OnyxClient(CONFIG) as client:
            analysis_dict = client.get_analysis(server, analysis_id)
        exitcode = 0

        return analysis_dict, exitcode


    def _set_analysis_attributes(self, analysis_dict: dict) -> None:
        "Sets class attributes from input dictionary"
        for key, value in analysis_dict.items():
            setattr(self, key, value)
