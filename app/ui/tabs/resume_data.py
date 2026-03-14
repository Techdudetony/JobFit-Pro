"""
ResumeData
----------
Central data model for the Resume Builder.
All form sections read/write into this dataclass.
Supports serialization to/from dict for session persistence.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PersonalInfo:
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    website: str = ""


@dataclass
class WorkEntry:
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    bullets: list = field(default_factory=list)  # list of str

    def bullets_text(self) -> str:
        return "\n".join(self.bullets)

    def set_bullets_from_text(self, text: str):
        self.bullets = [
            line.lstrip("•-– ").strip()
            for line in text.splitlines()
            if line.strip()
        ]


@dataclass
class EducationEntry:
    degree: str = ""
    school: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    notes: str = ""


@dataclass
class SkillEntry:
    name: str = ""
    proficiency: str = "Proficient"  # Beginner | Familiar | Proficient | Expert


@dataclass
class ProjectEntry:
    name: str = ""
    description: str = ""
    technologies: str = ""
    url: str = ""
    date: str = ""


@dataclass
class CertificationEntry:
    name: str = ""
    issuer: str = ""
    date: str = ""
    url: str = ""


@dataclass
class ResumeData:
    personal:       PersonalInfo          = field(default_factory=PersonalInfo)
    summary:        str                   = ""
    experience:     list[WorkEntry]       = field(default_factory=list)
    education:      list[EducationEntry]  = field(default_factory=list)
    skills:         list[SkillEntry]      = field(default_factory=list)
    projects:       list[ProjectEntry]    = field(default_factory=list)
    certifications: list[CertificationEntry] = field(default_factory=list)
    awards:         list[str]             = field(default_factory=list)

    # ------------------------------------------------------------------
    def to_plain_text(self) -> str:
        """Convert to plain text suitable for ResumeStyleEngine."""
        lines = []
        p = self.personal

        if p.name:
            lines.append(p.name)
        parts = []
        if p.title:    parts.append(p.title)
        if p.location: parts.append(p.location)
        if parts:      lines.append("  |  ".join(parts))

        contact = []
        if p.phone:    contact.append(p.phone)
        if p.email:    contact.append(p.email)
        if p.linkedin: contact.append(p.linkedin)
        if p.website:  contact.append(p.website)
        if contact:    lines.append("   ".join(contact))

        lines.append("")

        if self.summary:
            lines += ["SUMMARY", self.summary, ""]

        if self.experience:
            lines.append("EXPERIENCE")
            for job in self.experience:
                end = "Present" if job.current else job.end_date
                date_str = f"{job.start_date} – {end}" if job.start_date else end
                lines.append(f"{job.title}   {date_str}")
                if job.company or job.location:
                    lines.append(f"{job.company}, {job.location}".strip(", "))
                for b in job.bullets:
                    if b.strip():
                        lines.append(f"- {b.strip()}")
                lines.append("")

        if self.education:
            lines.append("EDUCATION")
            for ed in self.education:
                end = ed.end_date or ""
                lines.append(f"{ed.degree}   {end}")
                if ed.school:
                    loc = f"{ed.school}, {ed.location}".strip(", ")
                    lines.append(loc)
                if ed.gpa:
                    lines.append(f"GPA: {ed.gpa}")
                if ed.notes:
                    lines.append(ed.notes)
                lines.append("")

        if self.skills:
            lines.append("SKILLS")
            by_level: dict[str, list[str]] = {}
            for s in self.skills:
                by_level.setdefault(s.proficiency, []).append(s.name)
            for level in ["Expert", "Proficient", "Familiar", "Beginner"]:
                if level in by_level:
                    lines.append(f"{level}: " + ", ".join(by_level[level]))
            lines.append("")

        if self.projects:
            lines.append("PROJECTS")
            for proj in self.projects:
                header = proj.name
                if proj.date: header += f"   {proj.date}"
                lines.append(header)
                if proj.technologies:
                    lines.append(f"Technologies: {proj.technologies}")
                if proj.description:
                    for l in proj.description.splitlines():
                        if l.strip():
                            lines.append(f"- {l.strip()}")
                if proj.url:
                    lines.append(proj.url)
                lines.append("")

        if self.certifications:
            lines.append("CERTIFICATIONS")
            for cert in self.certifications:
                line = cert.name
                if cert.issuer: line += f" — {cert.issuer}"
                if cert.date:   line += f"   {cert.date}"
                lines.append(line)
                if cert.url:    lines.append(cert.url)
            lines.append("")

        if self.awards:
            lines.append("AWARDS / RECOGNITIONS / VOLUNTEER WORK")
            for a in self.awards:
                if a.strip():
                    lines.append(f"- {a.strip()}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ResumeData":
        rd = cls()
        if "personal" in d:
            rd.personal = PersonalInfo(**d["personal"])
        rd.summary = d.get("summary", "")
        rd.experience = [WorkEntry(**e) for e in d.get("experience", [])]
        rd.education  = [EducationEntry(**e) for e in d.get("education", [])]
        rd.skills     = [SkillEntry(**s) for s in d.get("skills", [])]
        rd.projects   = [ProjectEntry(**p) for p in d.get("projects", [])]
        rd.certifications = [CertificationEntry(**c)
                             for c in d.get("certifications", [])]
        rd.awards = d.get("awards", [])
        return rd