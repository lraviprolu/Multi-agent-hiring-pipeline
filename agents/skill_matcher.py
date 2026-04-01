import json
from groq import Groq
from models.candidate import CandidateProfile, MatchResult


class SkillMatcherAgent:
    def __init__(self, client: Groq):
        self.client = client
        self.model = "llama-3.3-70b-versatile"

    def run(self, candidate: CandidateProfile, job_description: str) -> MatchResult:
        system_prompt = """You are a technical recruiter evaluating candidate-job fit.
Compare the candidate's skills and experience against the job description.
Return ONLY a valid JSON object with these exact keys:
{
  "score": 0.0,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "reasoning": "brief explanation of the score"
}
Score must be a number between 0 and 100. Do not include any text outside the JSON object."""

        candidate_summary = f"""
Candidate: {candidate.name}
Years of Experience: {candidate.years_of_experience}
Skills: {', '.join(candidate.skills)}
Education: {candidate.education}
Previous Roles: {', '.join(candidate.previous_roles)}
Summary: {candidate.summary}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Candidate Profile:\n{candidate_summary}\n\nJob Description:\n{job_description}",
                },
            ],
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())

        return MatchResult(
            score=float(data.get("score", 0)),
            matched_skills=data.get("matched_skills", []),
            missing_skills=data.get("missing_skills", []),
            reasoning=data.get("reasoning", ""),
        )
