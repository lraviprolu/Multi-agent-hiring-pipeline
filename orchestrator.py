import os
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from utils.file_reader import read_resume
from agents.resume_parser import ResumeParserAgent
from agents.skill_matcher import SkillMatcherAgent
from agents.interview_planner import InterviewPlannerAgent
from agents.gap_analysis import GapAnalysisAgent

console = Console()
SKILL_MATCH_THRESHOLD = 85.0


class HiringPipelineOrchestrator:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables.")
        self.client = Groq(api_key=api_key)

        self.resume_parser = ResumeParserAgent(self.client)
        self.skill_matcher = SkillMatcherAgent(self.client)
        self.interview_planner = InterviewPlannerAgent(self.client)
        self.gap_analysis = GapAnalysisAgent(self.client)

    def run(self, resume_path: str, job_description: str):
        console.print(Panel.fit(
            "[bold cyan]Enterprise Hiring Pipeline[/bold cyan]\n[dim]Multi-Agent Orchestration[/dim]",
            box=box.DOUBLE
        ))

        # ── Agent 1: Resume Parser ──────────────────────────────────────────
        console.print("\n[bold yellow]► Agent 1: Resume Parser[/bold yellow]")
        resume_text = read_resume(resume_path)
        candidate = self.resume_parser.run(resume_text)

        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Field", style="dim")
        table.add_column("Value")
        table.add_row("Name", candidate.name)
        table.add_row("Email", candidate.email)
        table.add_row("Experience", f"{candidate.years_of_experience} years")
        table.add_row("Education", candidate.education)
        table.add_row("Skills", ", ".join(candidate.skills))
        table.add_row("Roles", "\n".join(candidate.previous_roles))
        console.print(table)

        # ── Agent 2: Skill Matcher ──────────────────────────────────────────
        console.print("\n[bold yellow]► Agent 2: Skill Matcher[/bold yellow]")
        match = self.skill_matcher.run(candidate, job_description)

        score_color = "green" if match.score > SKILL_MATCH_THRESHOLD else "red"
        console.print(f"  Match Score: [{score_color}]{match.score:.1f}%[/{score_color}]")
        console.print(f"  Matched Skills: [green]{', '.join(match.matched_skills)}[/green]")
        console.print(f"  Missing Skills: [red]{', '.join(match.missing_skills)}[/red]")
        console.print(f"  Reasoning: [dim]{match.reasoning}[/dim]")

        # ── Conditional Routing ─────────────────────────────────────────────
        if match.score > SKILL_MATCH_THRESHOLD:
            console.print(f"\n[bold green]✓ Score {match.score:.1f}% > {SKILL_MATCH_THRESHOLD}% → Routing to Interview Planner[/bold green]")

            # ── Agent 3: Interview Planner ──────────────────────────────────
            console.print("\n[bold yellow]► Agent 3: Interview Planner[/bold yellow]")
            plan = self.interview_planner.run(candidate, match)

            console.print(Panel(
                "\n".join([f"[bold]{i+1}.[/bold] {q}" for i, q in enumerate(plan.questions)]),
                title=f"[cyan]Interview Questions for {plan.candidate_name}[/cyan]",
                box=box.ROUNDED
            ))

        else:
            console.print(f"\n[bold red]✗ Score {match.score:.1f}% ≤ {SKILL_MATCH_THRESHOLD}% → Routing to Gap Analysis[/bold red]")

            # ── Agent 4: Gap Analysis ───────────────────────────────────────
            console.print("\n[bold yellow]► Agent 4: Gap Analysis[/bold yellow]")
            report = self.gap_analysis.run(candidate, match)

            console.print(Panel(
                f"[bold]Missing Skills:[/bold] [red]{', '.join(report.missing_skills)}[/red]\n\n"
                f"[bold]Recommendations:[/bold]\n{report.recommendations}",
                title=f"[cyan]Gap Report for {report.candidate_name}[/cyan]",
                box=box.ROUNDED
            ))

        console.print("\n[bold cyan]Pipeline complete.[/bold cyan]\n")
