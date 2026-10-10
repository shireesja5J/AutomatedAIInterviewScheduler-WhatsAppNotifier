import re
from dotenv import load_dotenv

load_dotenv()


def analyze_email(subject, body):
    """
    Detect genuine interview/assessment emails using
    context-aware scoring instead of simple keyword matching.
    """

    try:
        subject_clean = re.sub(r"\s+", " ", subject or "").strip()
        body_clean = re.sub(r"\s+", " ", body or "").strip()

        # Subject gets more importance than body
        subject_lower = subject_clean.lower()
        body_lower = body_clean.lower()

        # Limit body size so random footer/newsletter content
        # doesn't influence classification too much
        body_lower = body_lower[:12000]

        content = f"{subject_lower} {body_lower}"

        # -------------------------------------------------
        # STRONG INTERVIEW SIGNALS
        # -------------------------------------------------

        strong_interview = [
            "interview scheduled",
            "interview invitation",
            "invited to interview",
            "interview invite",
            "schedule your interview",
            "schedule interview",
            "interview has been scheduled",
            "your interview is scheduled",
            "technical interview",
            "technical round",
            "final interview",
            "hr interview",
            "hr round",
            "managerial interview",
            "behavioral interview",
            "interview appointment",
            "interview details",
            "interview confirmation",
            "interview link",
            "interview meeting",
            "interview date",
            "interview time",
            "meet our hiring team",
            "speak with our hiring team"
        ]

        # -------------------------------------------------
        # WEAK INTERVIEW SIGNALS
        # -------------------------------------------------

        weak_interview = [
            "interview",
            "screening",
            "phone screen",
            "video interview",
            "onsite interview",
            "virtual interview",
            "in-person interview",
            "zoom interview",
            "google meet interview",
            "teams interview"
        ]

        # -------------------------------------------------
        # ASSESSMENT SIGNALS
        # -------------------------------------------------

        strong_assessment = [
            "coding assessment",
            "coding challenge",
            "online assessment",
            "technical assessment",
            "technical test",
            "online test",
            "coding test",
            "assessment link",
            "assessment invitation",
            "assessment invitation",
            "complete the assessment",
            "take the assessment",
            "assessment is scheduled",
            "aptitude assessment",
            "programming assessment",
            "hackerrank assessment",
            "codility assessment",
            "test link",
            "assessment deadline"
        ]

        weak_assessment = [
            "assessment",
            "coding challenge",
            "coding test",
            "online test",
            "aptitude test",
            "technical test"
        ]

        # -------------------------------------------------
        # NEGATIVE SIGNALS
        # -------------------------------------------------

        # These words often appear in normal job/newsletter emails
        # and should NOT make an email an interview.
        negative_signals = [
            "job alert",
            "job alerts",
            "jobs you may like",
            "recommended jobs",
            "new jobs",
            "latest jobs",
            "job opportunities",
            "career opportunities",
            "career newsletter",
            "hiring now",
            "we are hiring",
            "now hiring",
            "job opening",
            "job openings",
            "vacancy",
            "vacancies",
            "job search",
            "career fair",
            "recruitment newsletter",
            "recruitment update",
            "employment opportunities",
            "explore careers",
            "check out our jobs",
            "apply now",
            "applications are open",
            "application received",
            "application submitted",
            "thank you for applying",
            "thanks for applying",
            "your application",
            "application status"
        ]

        # -------------------------------------------------
        # SCORING
        # -------------------------------------------------

        interview_score = 0
        assessment_score = 0

        reasons = []

        # Strong interview signals
        for keyword in strong_interview:

            if keyword in subject_lower:
                interview_score += 5
                reasons.append(f"subject:{keyword}")

            elif keyword in body_lower:
                interview_score += 4
                reasons.append(f"body:{keyword}")

        # Weak interview signals
        for keyword in weak_interview:

            if keyword in subject_lower:
                interview_score += 3
                reasons.append(f"subject:{keyword}")

            elif keyword in body_lower:
                interview_score += 2
                reasons.append(f"body:{keyword}")

        # Strong assessment signals
        for keyword in strong_assessment:

            if keyword in subject_lower:
                assessment_score += 5
                reasons.append(f"subject:{keyword}")

            elif keyword in body_lower:
                assessment_score += 4
                reasons.append(f"body:{keyword}")

        # Weak assessment signals
        for keyword in weak_assessment:

            if keyword in subject_lower:
                assessment_score += 3

            elif keyword in body_lower:
                assessment_score += 2

        # -------------------------------------------------
        # NEGATIVE SCORE
        # -------------------------------------------------

        negative_score = 0

        for keyword in negative_signals:

            if keyword in subject_lower:
                negative_score += 5

            elif keyword in body_lower:
                negative_score += 2

        # -------------------------------------------------
        # SCHEDULE SIGNALS
        # -------------------------------------------------

        schedule_patterns = [

            r"\b\d{1,2}:\d{2}\s*(?:am|pm)\b",

            r"\b\d{1,2}\s*(?:am|pm)\b",

            r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",

            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

            r"\b(?:january|february|march|april|may|june|july|"
            r"august|september|october|november|december)"
            r"\s+\d{1,2}\b"
        ]

        has_schedule = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in schedule_patterns
        )

        if has_schedule:

            # A date/time is useful evidence only when
            # interview/assessment language also exists.
            if interview_score > 0:
                interview_score += 3
                reasons.append("schedule_information")

            if assessment_score > 0:
                assessment_score += 3

        # -------------------------------------------------
        # CALENDAR / MEETING SIGNALS
        # -------------------------------------------------

        meeting_signals = [
            "calendar invitation",
            "calendar invite",
            "meeting invitation",
            "meeting scheduled",
            "meeting details",
            "join the meeting",
            "join meeting",
            "meeting link",
            "google meet",
            "microsoft teams",
            "zoom"
        ]

        meeting_score = 0

        for keyword in meeting_signals:

            if keyword in subject_lower:
                meeting_score += 3

            elif keyword in body_lower:
                meeting_score += 2

        # Meeting alone should NOT mean interview.
        # It only helps if interview language is also present.
        if meeting_score > 0 and interview_score > 0:
            interview_score += meeting_score
            reasons.append("meeting_information")

        # -------------------------------------------------
        # FINAL DECISION
        # -------------------------------------------------

        # Strong negative evidence can reject weak matches
        if negative_score >= 5 and interview_score < 8:
            is_interview = False
        else:
            is_interview = interview_score >= 8

        is_assessment = (
            assessment_score >= 8
            and negative_score < 5
        )

        # If assessment is clearly detected, don't call it
        # an interview unless there is also strong interview evidence.
        if is_assessment and interview_score < 8:
            is_interview = False

        # -------------------------------------------------
        # EXTRACT INFORMATION
        # -------------------------------------------------

        company = extract_company(subject_clean, body_clean)

        date = extract_date(content)

        time = extract_time(content)

        interview_type = detect_type(content)

        result = {
            "is_interview": is_interview,
            "is_assessment": is_assessment,
            "company": company,
            "role": None,
            "date": date,
            "time": time,
            "timezone": None,
            "interview_type": interview_type,
            "confidence": calculate_confidence(
                interview_score,
                assessment_score,
                negative_score
            ),
            "score": {
                "interview": interview_score,
                "assessment": assessment_score,
                "negative": negative_score
            },
            "reasons": reasons[:10]
        }

        print("\n--------------------------------")
        print("EMAIL ANALYSIS")
        print("--------------------------------")
        print("Subject:", subject_clean)
        print("Interview score:", interview_score)
        print("Assessment score:", assessment_score)
        print("Negative score:", negative_score)
        print("Interview:", is_interview)
        print("Assessment:", is_assessment)
        print("Reasons:", reasons[:10])
        print("--------------------------------\n")

        return result

    except Exception as e:

        print(
            f"⚠️ Error analyzing email: {str(e)}"
        )

        return None


# =========================================================
# COMPANY EXTRACTION
# =========================================================

def extract_company(subject, body):

    text = f"{subject} {body}"

    patterns = [

        # "Interview at Google"
        r"\binterview\s+(?:at|with)\s+([A-Z][A-Za-z0-9&.\- ]{2,50})",

        # "Interview with Microsoft"
        r"\binterview\s+with\s+([A-Z][A-Za-z0-9&.\- ]{2,50})",

        # "Google Interview"
        r"^([A-Z][A-Za-z0-9&.\- ]{2,40})\s+interview\b",

        # "Your interview with Google"
        r"\binterview\s+with\s+([A-Z][A-Za-z0-9&.\- ]{2,50})",

        # "Google hiring team"
        r"\b([A-Z][A-Za-z0-9&.\- ]{2,40})\s+hiring\s+team"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            company = match.group(1).strip()

            # Remove common trailing words
            company = re.sub(
                r"\s+(team|regards|recruitment)$",
                "",
                company,
                flags=re.IGNORECASE
            )

            return company.strip()

    return None


# =========================================================
# DATE EXTRACTION
# =========================================================

def extract_date(content):

    patterns = [

        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",

        r"\b(?:monday|tuesday|wednesday|thursday|friday|"
        r"saturday|sunday)"
        r"(?:,\s*)?"
        r"\d{1,2}(?:st|nd|rd|th)?\b",

        r"\b(?:january|february|march|april|may|june|july|"
        r"august|september|october|november|december)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            content,
            re.IGNORECASE
        )

        if match:
            return match.group(0)

    return None


# =========================================================
# TIME EXTRACTION
# =========================================================

def extract_time(content):

    patterns = [

        r"\b\d{1,2}:\d{2}\s*(?:am|pm)\b",

        r"\b\d{1,2}\s*(?:am|pm)\b",

        r"\b\d{1,2}:\d{2}\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            content,
            re.IGNORECASE
        )

        if match:
            return match.group(0)

    return None


# =========================================================
# INTERVIEW TYPE
# =========================================================

def detect_type(content):

    if "technical interview" in content:
        return "technical"

    if "technical round" in content:
        return "technical"

    if "behavioral interview" in content:
        return "behavioral"

    if "hr interview" in content or "hr round" in content:
        return "HR"

    if "managerial interview" in content:
        return "managerial"

    if "phone screen" in content:
        return "phone screen"

    if "video interview" in content:
        return "video interview"

    if "onsite interview" in content:
        return "onsite"

    if "coding assessment" in content:
        return "coding assessment"

    if "assessment" in content:
        return "assessment"

    return "interview"


# =========================================================
# CONFIDENCE
# =========================================================

def calculate_confidence(
    interview_score,
    assessment_score,
    negative_score
):

    score = max(
        interview_score,
        assessment_score
    )

    score -= negative_score

    if score >= 15:
        return "high"

    if score >= 10:
        return "medium"

    if score >= 8:
        return "low"

    return "none"
