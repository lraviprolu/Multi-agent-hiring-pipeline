import json
from groq import Groq
from models.candidate import CandidateProfile


class ResumeParserAgent:
    def __init__(self, client: Groq):
        self.client = client
        self.model = "llama-3.3-70b-versatile"

    def run(self, resume_text: str) -> CandidateProfile:
        system_prompt = """You are a resume parsing expert. Extract structured information from the resume text.
Return ONLY a valid JSON object with these exact keys:
{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "years_of_experience": 0.0,
  "skills": ["skill1", "skill2"],
  "education": "highest degree and institution",
  "previous_roles": ["role1 at company1", "role2 at company2"],
  "summary": "2-3 sentence professional summary"
}
Do not include any text outside the JSON object."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this resume:\n\n{resume_text}"},
            ],
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())

        return CandidateProfile(
            name=data.get("name", "Unknown"),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            years_of_experience=float(data.get("years_of_experience", 0)),
            skills=data.get("skills", []),
            education=data.get("education", ""),
            previous_roles=data.get("previous_roles", []),
            summary=data.get("summary", ""),
        )
