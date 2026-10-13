"""content — entry point. Every Firebase function this domain deploys, mapped to the
subdomain `main` module that defines it. Nothing is imported here; see the root main.py."""

FUNCTIONS: dict[str, str] = {
    "api_content_profile": "src.content.profile.main",
    "api_content_projects": "src.content.projects.main",
    "api_content_skills": "src.content.skills.main",
    "api_content_experience": "src.content.experience.main",
    "api_content_education": "src.content.education.main",
    "api_content_certifications": "src.content.certifications.main",
    "api_content_posts": "src.content.posts.main",
    "api_content_settings": "src.content.settings.main",
}
