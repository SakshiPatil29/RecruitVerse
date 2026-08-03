"""
AI-powered recruiter insights.

Each function builds a prompt from structured candidate/JD data (never
raw file bytes) and calls Ollama. If Ollama is unavailable, each falls
back to a simple rule-based version built from the same structured data,
reusing src.interview_assistant.question_generator and
src.explainability.score_explainer where they already cover the ground.
"""

from src.ai.ollama_client import generate
from src.explainability.score_explainer import generate_reason
from src.interview_assistant.question_generator import generate_questions


def _candidate_context(candidate):
    return (
        f"Name: {candidate.get('name')}\n"
        f"Experience: {candidate.get('experience_years')} years\n"
        f"Education: {candidate.get('education')}\n"
        f"Skills: {', '.join(candidate.get('skills', []))}\n"
        f"Certifications: {', '.join(candidate.get('certifications', []))}\n"
        f"Projects: {'; '.join(candidate.get('projects', [])[:5])}\n"
        f"Matched skills: {', '.join(candidate.get('matched_skills', []))}\n"
        f"Missing skills: {', '.join(candidate.get('missing_skills', []))}\n"
        f"Additional skills: {', '.join(candidate.get('additional_skills', []))}\n"
        f"Final match score: {candidate.get('final_score')}\n"
    )


def generate_summary(candidate):
    prompt = (
        "Summarize this candidate's resume for a recruiter in 4-6 concise bullet points. "
        "Focus on years of experience, strongest skills, and notable project/domain experience.\n\n"
        f"{_candidate_context(candidate)}"
    )
    result = generate(prompt, system="You are a concise technical recruiter assistant.")
    if result:
        return result

    skills = candidate.get("skills", [])
    return (
        f"• {candidate.get('experience_years', 0)} years of experience\n"
        f"• Key skills: {', '.join(skills[:5]) if skills else 'not listed'}\n"
        f"• Education: {candidate.get('education') or 'not specified'}"
    )


def generate_strengths_weaknesses(candidate):
    prompt = (
        "Based on this candidate's profile, list their strengths (things that match or exceed "
        "the job requirements) and weaknesses (skill gaps or shortfalls) as two short bullet lists, "
        "under headers 'Strengths:' and 'Weaknesses:'.\n\n"
        f"{_candidate_context(candidate)}"
    )
    result = generate(prompt, system="You are an honest, specific technical recruiter assistant.")
    if result:
        return result

    strengths = [f"✓ {s}" for s in candidate.get("matched_skills", [])[:6]]
    weaknesses = [f"• Missing {s}" for s in candidate.get("missing_skills", [])[:6]]
    strengths_text = "\n".join(strengths) if strengths else "✓ No standout matches identified"
    weaknesses_text = "\n".join(weaknesses) if weaknesses else "• No significant gaps identified"
    return f"Strengths:\n{strengths_text}\n\nWeaknesses:\n{weaknesses_text}"


def generate_hiring_recommendation(candidate):
    score = candidate.get("final_score", 0)

    prompt = (
        "Based on this candidate's match score and skill gaps, give a hiring recommendation "
        "(one of: Strongly Recommended, Recommended, Moderately Suitable, Not Recommended) "
        "followed by 2-3 sentences of reasoning.\n\n"
        f"{_candidate_context(candidate)}"
    )
    result = generate(prompt, system="You are a fair, evidence-based technical hiring advisor.")
    if result:
        return result

    if score >= 85:
        label = "Strongly Recommended"
    elif score >= 70:
        label = "Recommended"
    elif score >= 50:
        label = "Moderately Suitable"
    else:
        label = "Not Recommended"

    reason = generate_reason(score, candidate.get("matched_skills", []), candidate.get("missing_skills", []))
    return f"{label}\n\n{reason}"


def generate_explanation(candidate, rank=None):
    prompt = (
        f"Explain in 2-4 sentences why this candidate {'ranked #' + str(rank) if rank else 'received their score'}, "
        "referencing specific matched skills, experience, and any significant gaps.\n\n"
        f"{_candidate_context(candidate)}"
    )
    result = generate(prompt, system="You are a technical recruiter explaining a ranking decision.")
    if result:
        return result

    return generate_reason(
        candidate.get("final_score", 0),
        candidate.get("matched_skills", []),
        candidate.get("missing_skills", []),
    )


def generate_interview_questions(candidate, jd):
    prompt = (
        "Generate interview questions for this candidate for the given job, organized under these exact "
        "headers: 'Technical Questions:', 'Resume-Based Questions:', 'Project-Based Questions:', "
        "'Scenario-Based Questions:', 'HR Questions:'. 3-5 questions per section. Base the "
        "Resume-Based and Project-Based questions on the candidate's actual listed skills and projects, "
        "not generic questions.\n\n"
        f"{_candidate_context(candidate)}\n"
        f"Job required skills: {', '.join(jd.get('required_skills', []))}\n"
        f"Job preferred skills: {', '.join(jd.get('preferred_skills', []))}\n"
    )
    result = generate(prompt, system="You are an experienced technical interviewer preparing candidate-specific questions.")
    if result:
        return result

    # Rule-based fallback using the original question_generator.
    technical = generate_questions(candidate.get("matched_skills", []) or candidate.get("skills", []))
    project_qs = [f"Walk me through your project: {p}" for p in candidate.get("projects", [])[:4]]
    resume_qs = [
        f"Tell me more about your experience with {s}." for s in candidate.get("skills", [])[:4]
    ]
    scenario_qs = [
        f"How would you approach a task requiring {s} under a tight deadline?"
        for s in candidate.get("matched_skills", [])[:3]
    ]
    hr_qs = [
        "Why are you interested in this role?",
        "Describe your biggest professional challenge and how you handled it.",
    ]

    sections = [
        ("Technical Questions", technical),
        ("Resume-Based Questions", resume_qs),
        ("Project-Based Questions", project_qs or ["No projects listed to probe — ask about a recent significant contribution."]),
        ("Scenario-Based Questions", scenario_qs),
        ("HR Questions", hr_qs),
    ]
    return "\n\n".join(
        f"{title}:\n" + "\n".join(f"- {q}" for q in questions) for title, questions in sections
    )


def generate_resume_improvements(candidate, jd):
    prompt = (
        "Suggest 4-6 concrete, specific improvements this candidate could make to their resume "
        "to better match the job description below. Reference their actual missing skills.\n\n"
        f"{_candidate_context(candidate)}\n"
        f"Job required skills: {', '.join(jd.get('required_skills', []))}\n"
    )
    result = generate(prompt, system="You are a resume coach giving direct, actionable feedback.")
    if result:
        return result

    suggestions = [f"• Consider adding experience or projects with {s}" for s in candidate.get("missing_skills", [])[:5]]
    if not candidate.get("projects"):
        suggestions.append("• Add a Projects section with measurable outcomes")
    if not candidate.get("summary"):
        suggestions.append("• Add a concise professional summary at the top of the resume")
    return "\n".join(suggestions) if suggestions else "• Resume already covers all required skills well."


def generate_jd_summary(jd):
    prompt = (
        "Summarize this job description for a recruiter into four short sections: "
        "'Required Skills:', 'Preferred Skills:', 'Experience:', 'Education:'.\n\n"
        f"Required skills: {', '.join(jd.get('required_skills', []))}\n"
        f"Preferred skills: {', '.join(jd.get('preferred_skills', []))}\n"
        f"Experience required: {jd.get('experience_years')} years\n"
        f"Education: {jd.get('education')}\n"
        f"Certifications mentioned: {', '.join(jd.get('certifications', []))}\n"
    )
    result = generate(prompt, system="You are a concise recruiting coordinator.")
    if result:
        return result

    return (
        f"Required Skills: {', '.join(jd.get('required_skills', [])) or 'None specified'}\n"
        f"Preferred Skills: {', '.join(jd.get('preferred_skills', [])) or 'None specified'}\n"
        f"Experience: {jd.get('experience_years', 0)}+ years\n"
        f"Education: {jd.get('education') or 'Not specified'}"
    )
