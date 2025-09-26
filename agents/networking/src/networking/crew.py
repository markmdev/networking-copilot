from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

from networking.schemas import (
    IcebreakerOutput,
    LinkedInProfileAnalyzerOutput,
    SummaryOutput,
)
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Networking():
    """Networking crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def linkedin_profile_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['linkedin_profile_analyzer'], # type: ignore[index]
            verbose=True
        )

    @agent
    def summary_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['summary_generator'], # type: ignore[index]
            verbose=True
        )

    @agent
    def icebreaker_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['icebreaker_generator'], # type: ignore[index]
            verbose=True
        )

    @agent
    def profile_selector(self) -> Agent:
        return Agent(
            config=self.agents_config['profile_selector'], # type: ignore[index]
            verbose=True
        )

    @task
    def linkedin_profile_analyzer_task(self) -> Task:
        return Task(
            config=self.tasks_config['linkedin_profile_analyzer_task'], # type: ignore[index]
            name='linkedin_profile_analyzer_task',
            output_file='outputs/linkedin_profile_analyzer_task.json',
            output_json=LinkedInProfileAnalyzerOutput,
        )

    @task
    def summary_generator_task(self) -> Task:
        return Task(
            config=self.tasks_config['summary_generator_task'], # type: ignore[index]
            name='summary_generator_task',
            output_file='outputs/summary_generator_task.json',
            output_json=SummaryOutput,
        )

    @task
    def icebreaker_generator_task(self) -> Task:
        return Task(
            config=self.tasks_config['icebreaker_generator_task'], # type: ignore[index]
            name='icebreaker_generator_task',
            output_file='outputs/icebreaker_generator_task.json',
            output_json=IcebreakerOutput,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Networking crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
