import sys
from dotenv import load_dotenv
from orchestrator import HiringPipelineOrchestrator

load_dotenv()


def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <path_to_resume> <path_to_job_description>")
        print("Example: python main.py sample_data/sample_resume.pdf sample_data/job_description.txt")
        sys.exit(1)

    resume_path = sys.argv[1]
    jd_path = sys.argv[2]

    with open(jd_path, "r", encoding="utf-8") as f:
        job_description = f.read()

    pipeline = HiringPipelineOrchestrator()
    pipeline.run(resume_path, job_description)


if __name__ == "__main__":
    main()
