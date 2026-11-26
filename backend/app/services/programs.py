from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

LAST_VERIFIED = "2026-11-26"

PROGRAMS: list[dict[str, Any]] = [
    {
        "id": "gsoc-2026",
        "name": "Google Summer of Code 2026",
        "organization": "Google",
        "description": "Global program pairing new contributors with open-source organizations for a paid, mentored coding project.",
        "officialUrl": "https://summerofcode.withgoogle.com/",
        "applicationUrl": "https://summerofcode.withgoogle.com/",
        "status": "completed",
        "applicationOpenDate": "2026-03-16",
        "applicationDeadline": "2026-03-31T18:00:00Z",
        "duration": "8-22 weeks; program rules window ended 2026-11-11",
        "eligibility": "18 or older, non-embargoed country, limited prior open-source experience, official rules apply.",
        "requiredSkills": ["Git", "collaboration", "project-specific language"],
        "mentorship": True,
        "beginnerFriendly": True,
        "tags": ["mentorship", "paid", "student", "global"],
        "verificationSource": "https://developers.google.com/open-source/gsoc/timeline",
        "notes": "2026 timeline verified from the official Google developer documentation. Next cycle dates are not published here.",
    },
    {
        "id": "gssoc",
        "name": "GirlScript Summer of Code",
        "organization": "GirlScript Foundation",
        "description": "Open-source contribution program aimed at students and beginners, with mentors, projects and a leaderboard.",
        "officialUrl": "https://gssoc.girlscript.tech/",
        "applicationUrl": "https://gssoc.girlscript.tech/",
        "status": "status_unverified",
        "applicationOpenDate": None,
        "applicationDeadline": None,
        "duration": "Historically three months; confirm on the official site",
        "eligibility": "Check the official program site for current eligibility.",
        "requiredSkills": ["Git", "GitHub", "basic programming"],
        "mentorship": True,
        "beginnerFriendly": True,
        "tags": ["beginner", "students", "mentorship"],
        "verificationSource": "https://gssoc.girlscript.tech/",
        "notes": "Official program site still shows 2025 content. A 2026 edition is referenced by GirlScript but dates were not verified, so no dates are shown.",
    },
    {
        "id": "outreachy-dec-2026",
        "name": "Outreachy December 2026 cohort",
        "organization": "Outreachy",
        "description": "Paid remote internships for people facing underrepresentation in technology, with contributions before selection.",
        "officialUrl": "https://www.outreachy.org/",
        "applicationUrl": "https://www.outreachy.org/apply/",
        "status": "applications_closed",
        "applicationOpenDate": "2026-08-24T16:00:00Z",
        "applicationDeadline": "2026-11-09T16:00:00Z",
        "duration": "2026-12-07 to 2027-03-08",
        "eligibility": "18 or older by 2026-12-07, 30 hours/week, not a past Outreachy or GSoC intern, cohort rules by region and student status apply.",
        "requiredSkills": ["Git", "communication", "project-specific skills"],
        "mentorship": True,
        "beginnerFriendly": True,
        "tags": ["paid", "remote", "diversity", "internship"],
        "verificationSource": "https://www.outreachy.org/docs/applicant/",
        "notes": "Final application deadline passed. Accepted interns are announced 2026-11-30. Watch the official announcement list for the next round.",
    },
    {
        "id": "lfx-mentorship",
        "name": "LFX Mentorship",
        "organization": "Linux Foundation",
        "description": "Paid, mentored contribution terms across Linux Foundation projects, with per-program skill requirements.",
        "officialUrl": "https://mentorship.lfx.linuxfoundation.org/",
        "applicationUrl": "https://mentorship.lfx.linuxfoundation.org/programs",
        "status": "applications_open",
        "applicationOpenDate": None,
        "applicationDeadline": None,
        "duration": "Per-program terms, commonly around 12 weeks",
        "eligibility": "18 or older, consistent weekly commitment, up to three applications, one LFX mentorship per career.",
        "requiredSkills": ["Git", "project-specific technologies"],
        "mentorship": True,
        "beginnerFriendly": True,
        "tags": ["paid", "cloud", "linux", "rolling"],
        "verificationSource": "https://mentorship.lfx.linuxfoundation.org/",
        "notes": "Official site reported programs accepting applications at verification time. Each program page lists its own deadline.",
    },
    {
        "id": "wieos-2026",
        "name": "Women in Energy Open Source Mentorship (WIEOS)",
        "organization": "Open Energy Transition / LF Energy",
        "description": "Mentorship programme for women in energy and climate open source, with technical and non-technical tracks.",
        "officialUrl": "https://mentorship.lfx.linuxfoundation.org/programs/633c2c60-1be0-4aa5-913e-afa7e3fe26fd",
        "applicationUrl": "https://mentorship.lfx.linuxfoundation.org/programs/633c2c60-1be0-4aa5-913e-afa7e3fe26fd",
        "status": "applications_open",
        "applicationOpenDate": None,
        "applicationDeadline": "2026-12-12",
        "duration": "16-20 weeks",
        "eligibility": "Open to different starting points including non-coders, data analysts and experienced developers; see official programme page.",
        "requiredSkills": ["Python", "Git", "GitHub", "optional GIS/SQL"],
        "mentorship": True,
        "beginnerFriendly": True,
        "tags": ["python", "energy", "beginner", "mentorship", "women"],
        "verificationSource": "https://mentorship.lfx.linuxfoundation.org/programs/633c2c60-1be0-4aa5-913e-afa7e3fe26fd",
        "notes": "Application close date shown on the official LFX program page at verification time.",
    },
    {
        "id": "season-of-kde-2026",
        "name": "Season of KDE 2026",
        "organization": "KDE",
        "description": "Community outreach programme with paid or volunteer code and non-code projects in the KDE ecosystem.",
        "officialUrl": "https://season.kde.org/",
        "applicationUrl": "https://season.kde.org/",
        "status": "completed",
        "applicationOpenDate": "2025-12-15",
        "applicationDeadline": "2026-01-14",
        "duration": "2026-01-23 to 2026-03-20",
        "eligibility": "Open to contributors worldwide; selection favours early community engagement.",
        "requiredSkills": ["Qt/C++ or KDE-specific skills", "communication"],
        "mentorship": True,
        "beginnerFriendly": True,
        "tags": ["kde", "desktop", "mentorship"],
        "verificationSource": "https://season.kde.org/",
        "notes": "2026 dates verified on the official site. A 2027 season is not yet verified.",
    },
    {
        "id": "mlh-fellowship",
        "name": "MLH Fellowship",
        "organization": "Major League Hacking",
        "description": "Remote 12-week learning program with tracks in software engineering, production engineering and Web3.",
        "officialUrl": "https://fellowship.mlh.io/",
        "applicationUrl": "https://fellowship.mlh.io/apply",
        "status": "applications_closed",
        "applicationOpenDate": None,
        "applicationDeadline": "2026-04-30",
        "duration": "12 weeks; batches run multiple times per year",
        "eligibility": "18 or older, non-embargoed residence, 20 hours/week, English proficiency, one prior MLH event.",
        "requiredSkills": ["one programming language", "collaboration"],
        "mentorship": True,
        "beginnerFriendly": True,
        "tags": ["remote", "fallback", "web3", "devops"],
        "verificationSource": "https://fellowship.mlh.io/apply",
        "notes": "Summer 2026 deadline verified from the official application page. Later batch dates were not verified; check the official apply page.",
    },
    {
        "id": "hacktoberfest-2026",
        "name": "Hacktoberfest 2026",
        "organization": "MLH and DEV",
        "description": "October community celebration of open source with in-person Fests and online activities focused on open-source AI.",
        "officialUrl": "https://hacktoberfest.com/",
        "applicationUrl": "https://hacktoberfest.com/my/",
        "status": "completed",
        "applicationOpenDate": None,
        "applicationDeadline": None,
        "duration": "October 2026; concluded 2026-10-31",
        "eligibility": "Participants 13 or older, subject to country eligibility rules; individual events may add rules.",
        "requiredSkills": ["Git", "GitHub"],
        "mentorship": False,
        "beginnerFriendly": True,
        "tags": ["october", "events", "beginner"],
        "verificationSource": "https://hacktoberfest.com/",
        "notes": "2026 event concluded on 2026-10-31 per the official site. Pull requests no longer count toward rewards in 2026.",
    },
]

VALID_STATUSES = {"upcoming", "applications_open", "applications_closed", "ongoing", "completed", "status_unverified"}


def list_programs(
    *,
    status: str | None = None,
    search: str | None = None,
    beginner_friendly: bool | None = None,
    mentorship: bool | None = None,
    technology: str | None = None,
    upcoming_days: int | None = None,
) -> list[dict[str, Any]]:
    if status and status not in VALID_STATUSES:
        raise ValueError("Unknown program status.")
    results = []
    today = datetime.now(timezone.utc).date()
    for program in PROGRAMS:
        if status and program["status"] != status:
            continue
        if beginner_friendly is not None and program["beginnerFriendly"] != beginner_friendly:
            continue
        if mentorship is not None and program["mentorship"] != mentorship:
            continue
        if technology:
            haystack = " ".join(program["requiredSkills"] + program["tags"]).lower()
            if technology.lower() not in haystack:
                continue
        if search:
            needle = search.lower()
            haystack = " ".join(str(program[key]) for key in ("name", "organization", "description", "tags", "requiredSkills")).lower()
            if needle not in haystack:
                continue
        if upcoming_days is not None:
            deadline = program["applicationDeadline"]
            if not deadline:
                continue
            deadline_date = date.fromisoformat(deadline[:10])
            delta = (deadline_date - today).days
            if delta < 0 or delta > upcoming_days:
                continue
        results.append({**program, "lastVerified": LAST_VERIFIED})
    return results
