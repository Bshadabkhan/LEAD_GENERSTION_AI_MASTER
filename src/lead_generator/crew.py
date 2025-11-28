from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from crewai_tools import SerperDevTool, ScrapeWebsiteTool

load_dotenv()

# Tools
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

# Define your schema
class LeadOutput(BaseModel):
    company_name: Optional[str] = Field(description="The name of the company")
    annual_revenue: Optional[str] = Field(description="Annual revenue of the company")
    location: Optional[Dict[str, str]] = Field(description="Location with city and country fields")
    website_url: Optional[str] = Field(description="Company website URL")
    review: Optional[str] = Field(description="Description of what the company does")
    num_employees: Optional[int] = Field(description="Number of employees")
    key_decision_makers: Optional[List[Dict[str, str]]] = Field(description="List of key people with their LinkedIn profiles")
    score: Optional[int] = Field(description="Fit score on a scale of 1-10")

# Crew
@CrewBase
class LeadGenerator():
	"""LeadGenerator crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def lead_generator(self) -> Agent:
		return Agent(
			config=self.agents_config['lead_generator'],
			tools=[search_tool, scrape_tool],
			verbose=True
		)
	
	@agent
	def contact_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['contact_agent'],
			tools=[search_tool, scrape_tool],
			verbose=True
		)

	@agent 
	def lead_qualifier(self) -> Agent:
		return Agent(
			config=self.agents_config['lead_qualifier'],
			verbose=True
		)	

	@agent
	def sales_manager(self) -> Agent:
		return Agent(
			config=self.agents_config['sales_manager'],
			tools=[],
			verbose=True
		)	

	@task
	def lead_generation_task(self) -> Task:
		return Task(
			config=self.tasks_config['lead_generation_task'],
			output_pydantic=LeadOutput
		)

	@task
	def contact_research_task(self) -> Task:
		return Task(
			config=self.tasks_config['contact_research_task'],
			context=[self.lead_generation_task()],
			#output_pydantic=LeadOutput,
		)
	
	@task
	def lead_qualification_task(self) -> Task:
		return Task(
			config=self.tasks_config['lead_qualification_task'],
			context=[self.lead_generation_task(), self.contact_research_task()],
			output_pydantic=LeadOutput,
			
		)

	@task
	def sales_management_task(self) -> Task:
		return Task(
			config=self.tasks_config['sales_management_task'],
			context=[self.lead_generation_task(), self.lead_qualification_task(), self.contact_research_task()],
			output_pydantic=LeadOutput
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the LeadGenerator crew"""
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True,
			#manager_llm="gpt-4o",
			#planning=True,
			#memory=True,
			usage_metrics={}
		)

	
