"""Shared execution helpers for running the Networking crew."""

from __future__ import annotations

import json
from pathlib import Path
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.crews.crew_output import CrewOutput

from networking.crew import Networking
from networking.schemas import ProfileSelectionOutput


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = Path(__file__).resolve().parent / "config"


def _extract_structured_outputs(result: CrewOutput) -> Dict[str, Any]:
    """Convert CrewOutput into a mapping keyed by task name."""

    outputs: Dict[str, Any] = {}
    for index, task_output in enumerate(result.tasks_output):
        name = task_output.name or f"task_{index}"
        if task_output.json_dict is not None:
            outputs[name] = task_output.json_dict
        else:
            payload: Any
            if task_output.raw:
                try:
                    payload = json.loads(task_output.raw)
                except json.JSONDecodeError:
                    payload = task_output.raw
            else:
                payload = None
            outputs[name] = payload
    return outputs


def _write_task_outputs(tasks: list[Task], outputs: Dict[str, Any]) -> None:
    """Persist validated task outputs to their configured files as JSON."""

    for task in tasks:
        if not task.name or not task.output_file:
            continue
        if task.name not in outputs:
            continue

        output_path = Path(task.output_file)
        if not output_path.is_absolute():
            output_path = _PROJECT_ROOT / output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open('w', encoding='utf-8') as handle:
            json.dump(outputs[task.name], handle, indent=2)


def run_networking_crew(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the Networking crew and return structured task outputs."""

    networking = Networking()
    crew = networking.crew()

    result = crew.kickoff(inputs={"linkedin_profile": json.dumps(profile, indent=2)})
    outputs = _extract_structured_outputs(result)
    _write_task_outputs(networking.tasks, outputs)
    return outputs


def select_profile(candidates: List[Dict[str, Any]], search_criteria: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """Run the profile selector crew to choose the best candidate profile."""

    if not candidates:
        raise ValueError("No candidate profiles provided for selection")

    agent_config = _agents_config()['profile_selector']
    task_config = _tasks_config()['profile_selector_task']

    selector_agent = Agent(config=agent_config, verbose=True)
    selector_task = Task(
        config=task_config,
        agent=selector_agent,
        name='profile_selector_task',
        output_file='outputs/profile_selector_task.json',
        output_json=ProfileSelectionOutput,
    )

    crew = Crew(
        agents=[selector_agent],
        tasks=[selector_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff(inputs={
        "candidate_profiles": json.dumps(candidates, indent=2),
        "search_criteria": search_criteria,
    })

    outputs = _extract_structured_outputs(result)
    _write_task_outputs([selector_task], outputs)

    selection = outputs.get('profile_selector_task')
    if not isinstance(selection, dict):
        raise ValueError("Profile selector task returned no structured output")

    profile = selection.get("selected_profile")
    rationale = selection.get("rationale")
    if not isinstance(profile, dict):
        raise ValueError("Profile selector did not provide a selected_profile")

    return profile, rationale


@lru_cache(maxsize=1)
def _agents_config() -> Dict[str, Any]:
    with (_CONFIG_DIR / 'agents.yaml').open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=1)
def _tasks_config() -> Dict[str, Any]:
    with (_CONFIG_DIR / 'tasks.yaml').open('r', encoding='utf-8') as handle:
        return yaml.safe_load(handle)
