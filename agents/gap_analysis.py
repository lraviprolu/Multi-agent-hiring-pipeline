import json
from groq import Groq
from models.candidate import CandidateProfile, MatchResult, GapReport


class GapAnalysisAgent:
    def __init__(self, client: Groq):
        self.client = client
        self.model = "llama-3.3-70b-versatile"

    def run(self, candidate: CandidateProfile, match: MatchResult) -> GapReport:
        system_prompt = """You are a career development advisor reviewing a candidate's skill gaps.
Analyze the missing skills and provide actionable, specific recommendations.
Return ONLY a valid JSON object with this exact structure:
{
  "recommendations": "detailed paragraph with specific learning paths, courses, or certifications the candidate should pursue to bridge the gap"
}
Do not include any text outside the JSON object."""

        context = f"""
Candidate: {candidate.name}
Years of Experience: {candidate.years_of_experience}
Current Skills: {', '.join(candidate.skills)}
Missing Skills: {', '.join(match.missing_skills)}
Match Score: {match.score}%
Recruiter Reasoning: {match.reasoning}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Provide gap analysis and recommendations:\n{context}",
                },
            ],
            temperature=0.5,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())

        return GapReport(
            candidate_name=candidate.name,
            match_score=match.score,
            missing_skills=match.missing_skills,
            recommendations=data.get("recommendations", ""),
        )
