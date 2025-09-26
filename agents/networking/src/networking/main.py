#!/usr/bin/env python
import sys
import warnings
import json
from datetime import datetime

from networking.execution import run_networking_crew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    with open('data/mark_linkedin_data.json', 'r') as f:
        linkedin_data = json.load(f)
        profile = linkedin_data[0] if isinstance(linkedin_data, list) and linkedin_data else linkedin_data

        try:
            outputs = run_networking_crew(profile)
        except Exception as e:
            raise Exception(f"An error occurred while running the crew: {e}")

        print(json.dumps(outputs, indent=2))
