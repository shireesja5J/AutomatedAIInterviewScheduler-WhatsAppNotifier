# AI Interview Reminder

An automated system that monitors your Gmail for job interview emails, extracts interview details using AI, and sends you WhatsApp notifications.

## Features

- **Gmail Integration**: Automatically monitors unread emails
- **AI Analysis**: Uses OpenAI to detect interview emails and extract details
- **SQLite Database**: Stores all detected interviews
- **WhatsApp Notifications**: Sends formatted interview details via WhatsApp
- **Automatic Monitoring**: Checks emails every 5 minutes in the background
- **Console Fallback**: Logs WhatsApp messages to console when API credentials aren't configured

## Project Structure

```
interview-reminder/
├── main.py              # FastAPI application
├── gmail_service.py     # Gmail API integration
├── ai_analyzer.py       # OpenAI email analysis
├── whatsapp_service.py  # WhatsApp Cloud API integration
├── database.py          # SQLite database operations
├── scheduler.py         # Background email checking
├── auth.py              # Gmail authentication
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── credentials.json     # Gmail API credentials
└── interviews.db        # SQLite database (created automatically)
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key
WHATSAPP_ACCESS_TOKEN=your_meta_access_token
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id
WHATSAPP_TO_NUMBER=919XXXXXXXXX
```

### 3. Gmail Setup

- Your `credentials.json` file should already be in the project directory
- On first run, Google OAuth will prompt you to authorize the application
- A `token.json` file will be created to store your authentication

### 4. Run the Application

```bash
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`

## Usage

### Automatic Monitoring

The application automatically checks for new emails every 5 minutes in the background. No manual intervention needed.

### Manual Check

You can manually trigger an email check via API:

```bash
curl -X POST http://127.0.0.1:8000/check-emails
```

Or visit the API documentation at:
```
http://127.0.0.1:8000/docs
```

### WhatsApp Setup (Optional)

To enable actual WhatsApp messages:

1. Create a Meta Developer account at [developers.facebook.com](https://developers.facebook.com)
2. Create a WhatsApp Business App
3. Get your Access Token and Phone Number ID
4. Update the `.env` file with your credentials

**Without WhatsApp credentials**, the application will log messages to the console instead, allowing you to test all other functionality.

## How It Works

1. **Gmail Monitoring**: The scheduler checks for unread emails every 5 minutes
2. **AI Analysis**: Each email is analyzed by OpenAI to determine if it's an interview
3. **Data Extraction**: For interview emails, extracts:
   - Company name
   - Job role
   - Interview date
   - Interview time
   - Timezone
   - Interview type (technical/HR/assessment/other)
4. **Database Storage**: Saves interview details to SQLite
5. **WhatsApp Notification**: Sends formatted message with interview details

## Example WhatsApp Message

```
🚨 Interview Detected!

🏢 Company: Accenture

💼 Role: Software Engineer

📅 Date: 2024-08-20

⏰ Time: 11:00

🌍 Timezone: IST

🎯 Type: technical

Good luck! 🚀
```

## Database

The SQLite database (`interviews.db`) contains an `interviews` table with:
- `id`: Primary key
- `email_id`: Unique Gmail message ID
- `company`: Company name
- `role`: Job role
- `interview_date`: Interview date (YYYY-MM-DD)
- `interview_time`: Interview time (HH:MM)
- `timezone`: Timezone
- `interview_type`: Type of interview
- `whatsapp_sent`: Flag indicating if WhatsApp was sent

## Troubleshooting

### Gmail Authentication Issues

- Delete `token.json` and restart the application to re-authenticate
- Ensure your Google Cloud Console project has Gmail API enabled

### OpenAI API Issues

- Verify your API key in `.env`
- Check your OpenAI account has available credits

### WhatsApp Not Working

- Without credentials, messages will appear in console logs
- To enable actual WhatsApp, follow the WhatsApp Setup section above

## API Endpoints

- `GET /` - Health check and status
- `POST /check-emails` - Manually trigger email check

## License

MIT
