from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from gmail_service import get_new_emails
from ai_analyzer import analyze_email
from sms_service import send_sms_message, send_sms_simple_message
from database import (
    create_database,
    save_interview,
    claim_notification,
    finish_notification,
    get_recent_interviews,
)
from scheduler import start_scheduler
from auth import get_flow, get_gmail_credentials, save_credentials
import sys

# Gmail subjects may contain characters outside the Windows console code page.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

app = FastAPI(
    title="AI Interview Reminder"
)

def send_no_interview_notice():
    """Send an SMS update when an email check finds no interviews."""
    response = send_sms_simple_message(
        "No interview was found in your recent Gmail checks. I will keep monitoring and notify you when one is detected."
    )
    if response.get("success"):
        return True
    print(f"Could not send no-interview SMS update: {response.get('error', 'Unknown error')}")
    return False

def notify_interview(email_id, result):
    """Persist an interview and send its SMS alert at most once at a time."""
    save_interview(email_id, result)
    if not claim_notification(email_id):
        return False

    response = send_sms_message(
        company=result.get("company") or "Unknown",
        date=result.get("date") or "TBD",
        time=result.get("time") or "TBD",
        role=result.get("role"),
    )
    finish_notification(email_id, response.get("success", False))
    return response.get("success", False)

@app.on_event("startup")
def startup():
    create_database()
    # Start automatic email checking every 5 minutes and no-interview check every 30 minutes
    start_scheduler(check_emails_background, check_no_interviews)

@app.get("/", response_class=HTMLResponse)
def home():
    # Check if user is authenticated
    creds = get_gmail_credentials()
    auth_status = "âœ… Authenticated" if creds and creds.valid else "âŒ Not Authenticated"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Interview Reminder</title>
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1400px;
                margin: 0 auto;
                padding: 40px 20px;
                background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
                min-height: 100vh;
                color: #ffffff;
            }}
            .header {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: white;
                padding: 40px;
                border-radius: 24px;
                margin-bottom: 30px;
                box-shadow: 
                    0 25px 50px rgba(0, 0, 0, 0.3),
                    0 10px 20px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 3em;
                font-weight: 800;
                letter-spacing: -1px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            .header p {{
                margin: 0;
                font-size: 1.1em;
                opacity: 0.8;
                font-weight: 400;
            }}
            .status {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 20px;
                margin-bottom: 30px;
                box-shadow: 
                    0 15px 35px rgba(0, 0, 0, 0.2),
                    0 5px 15px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }}
            .status h2 {{
                margin: 0 0 15px 0;
                font-size: 1.5em;
                font-weight: 600;
                color: #ffffff;
            }}
            .status p {{
                margin: 8px 0;
                font-size: 1em;
                opacity: 0.9;
                color: rgba(255, 255, 255, 0.8);
            }}
            .status strong {{
                color: #ffffff;
                font-weight: 600;
            }}
            .status.running {{
                border-left: 4px solid #4CAF50;
            }}
            .button {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 16px 32px;
                border-radius: 16px;
                cursor: pointer;
                font-size: 15px;
                font-weight: 600;
                margin-right: 12px;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                box-shadow: 
                    0 8px 25px rgba(102, 126, 234, 0.4),
                    0 4px 10px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                text-transform: none;
                letter-spacing: 0.5px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .button:hover {{
                transform: translateY(-3px);
                box-shadow: 
                    0 12px 35px rgba(102, 126, 234, 0.5),
                    0 6px 15px rgba(0, 0, 0, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.3);
            }}
            .button:active {{
                transform: translateY(-1px);
                box-shadow: 
                    0 6px 20px rgba(102, 126, 234, 0.4),
                    0 3px 8px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
            }}
            .button:disabled {{
                background: rgba(255, 255, 255, 0.1);
                cursor: not-allowed;
                box-shadow: none;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .button.auth {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                box-shadow: 
                    0 8px 25px rgba(76, 175, 80, 0.4),
                    0 4px 10px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
            }}
            .button.auth:hover {{
                box-shadow: 
                    0 12px 35px rgba(76, 175, 80, 0.5),
                    0 6px 15px rgba(0, 0, 0, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
            }}
            .button.sms {{
                background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
                box-shadow: 
                    0 8px 25px rgba(37, 211, 102, 0.4),
                    0 4px 10px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
            }}
            .button.sms:hover {{
                box-shadow: 
                    0 12px 35px rgba(37, 211, 102, 0.5),
                    0 6px 15px rgba(0, 0, 0, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
            }}
            .emails-container {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 35px;
                border-radius: 24px;
                box-shadow: 
                    0 25px 50px rgba(0, 0, 0, 0.2),
                    0 10px 20px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
            }}
            .emails-container h2 {{
                margin: 0 0 25px 0;
                font-size: 1.8em;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: -0.5px;
            }}
            .email-item {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 25px;
                margin-bottom: 20px;
                border-radius: 16px;
                box-shadow: 
                    0 8px 20px rgba(0, 0, 0, 0.15),
                    0 2px 5px rgba(0, 0, 0, 0.05),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            .email-item:hover {{
                transform: translateY(-4px);
                box-shadow: 
                    0 12px 30px rgba(0, 0, 0, 0.2),
                    0 4px 10px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.15);
            }}
            .email-item.interview {{
                background: rgba(76, 175, 80, 0.1);
                border: 2px solid #4CAF50;
                box-shadow: 
                    0 12px 30px rgba(76, 175, 80, 0.2),
                    0 4px 10px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.08);
            }}
            .email-item.not-interview {{
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            .email-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }}
            .email-sender {{
                font-weight: 700;
                color: #ffffff;
                font-size: 1.1em;
                letter-spacing: -0.3px;
            }}
            .email-date {{
                color: rgba(255, 255, 255, 0.6);
                font-size: 0.9em;
                font-weight: 500;
            }}
            .email-subject {{
                font-weight: 600;
                color: #ffffff;
                margin-bottom: 15px;
                font-size: 1.15em;
                letter-spacing: -0.3px;
            }}
            .email-body {{
                color: rgba(255, 255, 255, 0.7);
                font-size: 0.95em;
                max-height: 100px;
                overflow-y: auto;
                line-height: 1.7;
            }}
            .interview-badge {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 25px;
                font-size: 0.85em;
                margin-left: 12px;
                font-weight: 600;
                box-shadow: 
                    0 4px 12px rgba(76, 175, 80, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .not-interview-badge {{
                background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 25px;
                font-size: 0.85em;
                margin-left: 12px;
                font-weight: 600;
                box-shadow: 
                    0 4px 12px rgba(244, 67, 54, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .assessment-badge {{
                background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 25px;
                font-size: 0.85em;
                margin-left: 12px;
                font-weight: 600;
                box-shadow: 
                    0 4px 12px rgba(255, 152, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .interview-details {{
                background: rgba(76, 175, 80, 0.15);
                padding: 20px;
                border-radius: 16px;
                margin-top: 15px;
                font-size: 0.9em;
                box-shadow: 
                    0 4px 12px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(76, 175, 80, 0.3);
            }}
            .interview-details strong {{
                color: #ffffff;
                font-weight: 600;
            }}
            .loading {{
                text-align: center;
                padding: 40px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 1.1em;
                font-weight: 500;
            }}
            .error {{
                color: #ff6b6b;
                padding: 20px;
                background: rgba(255, 107, 107, 0.1);
                border-radius: 16px;
                margin-bottom: 20px;
                box-shadow: 
                    0 4px 12px rgba(255, 107, 107, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 107, 107, 0.3);
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ðŸ¤– AI Interview Reminder</h1>
            <p>Automatically monitors Gmail for job interview emails</p>
        </div>

        <div class="status running">
            <h2>ðŸ“Š System Status</h2>
            <p><strong>Status:</strong> <span style="color: #4CAF50;">â— Running</span></p>
            <p><strong>Gmail Auth:</strong> {auth_status}</p>
            <p><strong>Monitoring:</strong> Gmail (every 5 minutes)</p>
            <p><strong>SMS Recipient:</strong> +91 78932 77617</p>
            {"" if creds and creds.valid else '<a href="/auth/login" class="button auth">ðŸ” Authenticate Gmail</a>'}
        </div>

        <div class="emails-container">
            <h2>ðŸ“§ Recent Emails Analysis</h2>
            <button class="button" onclick="checkEmails()">ðŸ”„ Check Latest 10 Emails (Auto SMS)</button>
            <button class="button sms" onclick="checkEmailsAndNotify()">Check Gmail + Send SMS Alerts</button>
            
            <div id="emails-container"></div>
        </div>

        <script>
            async function checkEmails() {{
                const container = document.getElementById('emails-container');
                container.innerHTML = '<div class="loading">ðŸ”„ Checking emails...</div>';
                
                try {{
                    const response = await fetch('/check-emails-display');
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    const data = await response.json();
                    if (data.error) {{
                        throw new Error(data.error);
                    }}
                    displayEmails(data.emails);
                }} catch (error) {{
                    container.innerHTML = '<div class="error">âŒ Error checking emails: ' + error.message + '<br><small>Please check the server console for details</small></div>';
                    console.error('Error:', error);
                }}
            }}

            async function checkEmailsAndNotify() {{
                const container = document.getElementById('emails-container');
                container.innerHTML = '<div class="loading">Checking Gmail and sending alerts for detected interviews...</div>';
                try {{
                    const response = await fetch('/check-emails', {{ method: 'POST' }});
                    const data = await response.json();
                    if (!response.ok || data.error) {{
                        throw new Error(data.error || `HTTP error! status: ${{response.status}}`);
                    }}
                    const sent = data.sms_alerts_sent || 0;
                    const found = data.interviews_found.length;
                    container.innerHTML = '<div class="interview-details">Checked ' + data.emails_checked +
                        ' emails. Detected ' + found + ' interview or assessment emails. Sent ' +
                        sent + ' interview SMS alert(s).' + (data.no_interview_message_sent ?
                        ' Sent a no-interview SMS update.' : (found === 0 ?
                        ' Could not send the no-interview SMS update; check the server logs.' : '')) + '</div>';
                }} catch (error) {{
                    container.innerHTML = '<div class="error">Gmail check failed: ' + error.message + '</div>';
                }}
            }}

            async function checkTop10() {{
                const container = document.getElementById('emails-container');
                container.innerHTML = '<div class="loading">ðŸ”„ Checking top 10 emails for interviews...</div>';
                
                try {{
                    const response = await fetch('/check-interviews');
                    if (!response.ok) {{
                        throw new Error(`HTTP error! status: ${{response.status}}`);
                    }}
                    const data = await response.json();
                    displayInterviews(data);
                }} catch (error) {{
                    container.innerHTML = '<div class="error">âŒ Error checking emails: ' + error.message + '<br><small>Please check the server console for details</small></div>';
                    console.error('Error:', error);
                }}
            }}

            function displayEmails(emails) {{
                const container = document.getElementById('emails-container');
                
                if (emails.length === 0) {{
                    container.innerHTML = '<div class="loading">ðŸ“­ No emails found</div>';
                    return;
                }}

                let html = '<h3>ðŸ“§ Latest 10 Emails</h3>';
                emails.forEach(email => {{
                    let interviewClass = 'not-interview';
                    let badge = '<span class="not-interview-badge">âŒ Not Interview</span>';
                    
                    if (email.is_interview) {{
                        interviewClass = 'interview';
                        badge = '<span class="interview-badge">âœ… Interview Detected</span>';
                    }} else if (email.is_assessment) {{
                        interviewClass = 'interview';
                        badge = '<span class="assessment-badge">ðŸ“ Assessment Detected</span>';
                    }}
                    
                    const interviewDetails = (email.is_interview || email.is_assessment) ? getInterviewDetails(email.analysis) : '';
                    html += `
                        <div class="email-item ${{interviewClass}}">
                            <div class="email-header">
                                <span class="email-sender">${{email.sender}}</span>
                                <span class="email-date">${{email.date}}</span>
                            </div>
                            <div class="email-subject">${{email.subject}} ${{badge}}</div>
                            <div class="email-body">${{email.body.substring(0, 200)}}...</div>
                            ${{interviewDetails}}
                        </div>
                    `;
                }});

                container.innerHTML = html;
            }}

            function displayInterviews(data) {{
                const container = document.getElementById('emails-container');
                
                let html = '<h3>ðŸŽ¯ Interview Detection Results (Top 10 Emails)</h3>';
                html += `<p><strong>Emails Checked:</strong> ${{data.emails_checked}}</p>`;
                html += `<p><strong>Interviews Found:</strong> ${{data.interviews_found}}</p>`;
                
                if (data.interviews_found > 0) {{
                    html += '<div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin-top: 10px;">';
                    html += '<h4 style="color: #4CAF50; margin-top: 0;">ðŸŽ‰ Interviews Detected!</h4>';
                    data.interview_details.forEach(interview => {{
                        html += getInterviewDetails(interview);
                    }});
                    html += '</div>';
                }} else {{
                    html += '<div style="background: #fff3e0; padding: 15px; border-radius: 5px; margin-top: 10px;">';
                    html += '<p style="color: #ff9800;">ðŸ“­ No interviews found in the top 10 emails</p>';
                    html += '</div>';
                }}

                container.innerHTML = html;
            }}

            function getInterviewDetails(analysis) {{
                return `
                    <div class="interview-details">
                        <strong>ðŸ¢ Company:</strong> ${{analysis.company || 'N/A'}}<br>
                        <strong>ðŸ’¼ Role:</strong> ${{analysis.role || 'N/A'}}<br>
                        <strong>ðŸ“… Date:</strong> ${{analysis.date || 'N/A'}}<br>
                        <strong>â° Time:</strong> ${{analysis.time || 'N/A'}}<br>
                        <strong>ðŸŒ Timezone:</strong> ${{analysis.timezone || 'N/A'}}<br>
                        <strong>ðŸŽ¯ Type:</strong> ${{analysis.interview_type || 'N/A'}}
                    </div>
                `;
            }}

            // Auto-check on page load
            window.onload = function() {{
                checkEmails();
            }};
        </script>
    </body>
    </html>
    """

@app.get("/auth/login")
def auth_login():
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(authorization_url)

@app.get("/auth/callback")
def auth_callback(request: Request):
    try:
        flow = get_flow()
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials
        save_credentials(credentials)
        return RedirectResponse(url="/")
    except Exception as e:
        # OAuth token exchange needs access to Google's token endpoint. Give the
        # user a useful response if that network request fails instead of a 500.
        print(f"Gmail OAuth callback failed: {e}")
        return HTMLResponse(
            "<h2>Gmail sign-in could not be completed</h2>"
            "<p>The app could not reach Google's OAuth service. Check your network "
            "or proxy settings, then try authenticating again.</p>"
            "<p><a href='/'>Return to the app</a></p>",
            status_code=503,
        )

@app.get("/check-emails-display")
def check_emails_display():
    try:
        emails = get_new_emails(limit=10)
        analyzed_emails = []
        interviews_found = []

        for email in emails:
            try:
                result = analyze_email(
                    email["subject"],
                    email["body"]
                )

                # Handle analysis failure
                if result is None:
                    print(f"Could not analyze email: {email['subject']}")
                    analyzed_emails.append({
                        "id": email["id"],
                        "sender": email["sender"],
                        "subject": email["subject"],
                        "body": email["body"],
                        "date": email["date"],
                        "is_interview": False,
                        "is_assessment": False,
                        "analysis": {"error": "Analysis failed - API error"}
                    })
                    continue

                analyzed_emails.append({
                    "id": email["id"],
                    "sender": email["sender"],
                    "subject": email["subject"],
                    "body": email["body"],
                    "date": email["date"],
                    "is_interview": result["is_interview"],
                    "is_assessment": result.get("is_assessment", False),
                    "analysis": result
                })

                if result["is_interview"] or result.get("is_assessment", False):
                    interviews_found.append({
                        "email": email,
                        "result": result
                    })
                    notify_interview(email["id"], result)
            except Exception as e:
                print(f"Error processing email {email['id']}: {str(e)}")
                analyzed_emails.append({
                    "id": email["id"],
                    "sender": email["sender"],
                    "subject": email["subject"],
                    "body": email["body"],
                    "date": email["date"],
                    "is_interview": False,
                    "is_assessment": False,
                    "analysis": {"error": str(e)}
                })

        # SMS alerts are sent individually for each interview found above
        # No summary message needed

        return {"emails": analyzed_emails}
    except Exception as e:
        print(f"Email display check failed: {e}")
        return {"emails": [], "error": str(e)}

@app.get("/check-interviews")
def check_interviews():
    try:
        emails = get_new_emails(limit=10)
        detected_interviews = []

        for email in emails:
            try:
                result = analyze_email(
                    email["subject"],
                    email["body"]
                )

                # Handle analysis failure
                if result is None:
                    print(f"Could not analyze email: {email['subject']}")
                    continue

                if result["is_interview"] or result.get("is_assessment", False):
                    detected_interviews.append(result)
                    notify_interview(email["id"], result)
                    print(f"Processed interview notification: {email['subject']}")
            except Exception as e:
                print(f"Error processing email {email['id']}: {str(e)}")

        return {
            "emails_checked": len(emails),
            "interviews_found": len(detected_interviews),
            "interview_details": detected_interviews
        }
    except Exception as e:
        print(f"Error in check_interviews: {str(e)}")
        return {
            "emails_checked": 0,
            "interviews_found": 0,
            "error": str(e)
        }

@app.post("/check-emails")
def check_emails():
    emails = get_new_emails(limit=10)
    detected_interviews = []
    sms_alerts_sent = 0

    for email in emails:
        result = analyze_email(
            email["subject"],
            email["body"]
        )

        # Handle analysis failure
        if result is None:
            print(f"Could not analyze email: {email['subject']}")
            continue

        if result["is_interview"] or result.get("is_assessment", False):
            detected_interviews.append(result)
            if notify_interview(email["id"], result):
                sms_alerts_sent += 1
            print(f"Processed interview notification: {email['subject']}")

    no_interview_message_sent = False
    if not detected_interviews:
        no_interview_message_sent = send_no_interview_notice()

    return {
        "emails_checked": len(emails),
        "interviews_found": detected_interviews,
        "sms_alerts_sent": sms_alerts_sent,
        "no_interview_message_sent": no_interview_message_sent
    }

def check_emails_background():
    """Background function for automatic email checking"""
    print("Checking for new emails...")
    try:
        result = check_emails()
        print(f"Checked {result['emails_checked']} emails; found {len(result['interviews_found'])} interviews")
    except Exception as e:
        print(f"Background Gmail check failed: {e}")

def check_no_interviews():
    """Background function to check if no interviews were found in the last 30 minutes"""
    print("Checking recent interview count...")
    recent_interviews = get_recent_interviews(hours=0.5)  # Check last 30 minutes
    
    if recent_interviews == 0:
        if send_no_interview_notice():
            print("Sent SMS no-interview update")
    else:
        print(f"Found {recent_interviews} recent interviews")

