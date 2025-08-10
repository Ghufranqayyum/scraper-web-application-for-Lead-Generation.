# Web Scraper Application

A Flask-based web application for scraping social media platforms including Facebook, Instagram, and X (Twitter).

## Features

- 🐦 X (Twitter) post scraping
- 📘 Facebook post scraping  
- 📸 Instagram post scraping
- 📧 Email results with CSV attachments
- 🌐 Web interface for easy usage

## Tech Stack

- **Backend**: Python Flask
- **Web Scraping**: Selenium, BeautifulSoup
- **Email**: SendGrid API
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Railway

## Setup

### Prerequisites
- Python 3.8+
- Chrome browser
- SendGrid account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/scraper-web-application.git
cd scraper-web-application
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export SENDGRID_API_KEY=your_sendgrid_api_key
export FROM_EMAIL=your_verified_email@example.com
Create your API Key and verify it
Set your own Flask Api secret key in app.py
set your facebook credential in facebook_scraper
```

4. Run the application:
```bash
python app.py
```

## Deployment

This application is configured for deployment on Railway:

1. Push code to GitHub
2. Connect GitHub repo to Railway
3. Set environment variables in Railway dashboard
4. Deploy automatically

## Environment Variables

- `SENDGRID_API_KEY`: Your SendGrid API key
- `FROM_EMAIL`: Verified sender email address
- `PORT`: Application port (set automatically by Railway)

## Usage

1. Open the web application
2. Select the social media platform
3. Enter the profile URL or post URL
4. Click "Start Scraping"
5. Receive results via email

## License

MIT License - see LICENSE file for details.

## Contributing

Pull requests are welcome. For major changes, please open an issue first.
