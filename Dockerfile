FROM python:3.12

ADD . /gpha_mscape_onyx_analysis_helper/
WORKDIR /gpha_mscape_onyx_analysis_helper
RUN pip install .
