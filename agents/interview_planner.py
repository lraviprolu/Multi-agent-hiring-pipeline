import json
from groq import Groq
from models.candidate import CandidateProfile, MatchResult, InterviewPlan


class InterviewPlannerAgent:
    def __init__(self, client: Groq):
        self.client = client
        self.model = "llama-3.3-70b-versatile"

    def run(self, candidate: CandidateProfile, match: MatchResult) -> InterviewPlan:
        system_prompt = """You are a senior technical interviewer.
Generate exactly 5 interview questions tailored to the candidate's background and matched skills.
Questions should be a mix of: technical depth, past experience, problem-solving, and situational.
Return ONLY a valid JSON object with this exact structure:
{
  "questions": [
    "Question 1",
    "Question 2",
    "Question 3",
    "Question 4",
    "Question 5"
  ]
}
Do not include any text outside the JSON object."""

        context = f"""
Candidate: {candidate.name}
Years of Experience: {candidate.years_of_experience}
Matched Skills: {', '.join(match.matched_skills)}
Previous Roles: {', '.join(candidate.previous_roles)}
Skill Match Score: {match.score}%
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Generate interview questions for this candidate:\n{context}",
                },
            ],
            temperature=0.7,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())

        return InterviewPlan(
            candidate_name=candidate.name,
            questions=data.get("questions", []),
        )
