from flask import Flask, render_template, request, jsonify, send_file, session
import threading
import os
import csv
import time
import uuid
from datetime import datetime
import json

# Import your existing scraper modules
from facebook_scraper import run_facebook_scraper
from instagram_scraper import run_instagram_scraper
from x_scraper import run_x_scraper

app = Flask(__name__)
app.secret_key = ''  # Change this to a secure secret key

# Global storage for scraping tasks
active_tasks = {}
completed_tasks = {}


class ScrapingTask:
    def __init__(self, task_id, platform, input_value, scrolls):
        self.task_id = task_id
        self.platform = platform
        self.input_value = input_value
        self.scrolls = scrolls
        self.status = 'waiting_for_manual_action'  # waiting_for_manual_action, running, completed, failed
        self.csv_path = None
        self.error_message = None
        self.created_at = datetime.now()
        self.completed_at = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    try:
        data = request.json
        platform = data.get('platform')
        input_value = data.get('input_value')
        scrolls = int(data.get('scrolls', 5))

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create task
        task = ScrapingTask(task_id, platform, input_value, scrolls)
        active_tasks[task_id] = task

        # Create flag file for the scraper
        flag_file = f"flag_{task_id}.txt"
        with open(flag_file, "w") as f:
            f.write("waiting")

        # Start scraping in background thread
        thread = threading.Thread(target=run_scraper, args=(task,))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Scraping task started. Please complete manual actions if required.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/task_status/<task_id>')
def get_task_status(task_id):
    task = active_tasks.get(task_id) or completed_tasks.get(task_id)

    if not task:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify({
        'task_id': task_id,
        'status': task.status,
        'platform': task.platform,
        'input_value': task.input_value,
        'scrolls': task.scrolls,
        'created_at': task.created_at.isoformat(),
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'error_message': task.error_message
    })


@app.route('/continue_scraping/<task_id>', methods=['POST'])
def continue_scraping(task_id):
    task = active_tasks.get(task_id)

    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if task.status != 'waiting_for_manual_action':
        return jsonify({'error': 'Task is not waiting for manual action'}), 400

    try:
        # Signal the scraper to continue
        flag_file = f"flag_{task_id}.txt"
        with open(flag_file, "w") as f:
            f.write("done")

        task.status = 'running'

        return jsonify({
            'success': True,
            'message': 'Signal sent to scraper. It will continue now.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/download_csv/<task_id>')
def download_csv(task_id):
    task = completed_tasks.get(task_id)

    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if task.status != 'completed' or not task.csv_path:
        return jsonify({'error': 'CSV file not available'}), 400

    if not os.path.exists(task.csv_path):
        return jsonify({'error': 'CSV file not found'}), 404

    return send_file(
        task.csv_path,
        as_attachment=True,
        download_name=f"{task.platform.lower()}_scraping_results_{task_id}.csv"
    )


@app.route('/view_csv/<task_id>')
def view_csv(task_id):
    task = completed_tasks.get(task_id)

    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if task.status != 'completed' or not task.csv_path:
        return jsonify({'error': 'CSV file not available'}), 400

    if not os.path.exists(task.csv_path):
        return jsonify({'error': 'CSV file not found'}), 404

    try:
        with open(task.csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)

        return jsonify({
            'success': True,
            'data': data,
            'total_records': len(data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/send_email/<task_id>', methods=['POST'])
def send_email(task_id):
    task = completed_tasks.get(task_id)

    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if task.status != 'completed' or not task.csv_path:
        return jsonify({'error': 'CSV file not available'}), 400

    try:
        data = request.json
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email address is required'}), 400

        # Use your existing email sending logic
        send_csv_email(task.csv_path, email, task.platform)

        return jsonify({
            'success': True,
            'message': f'CSV file sent to {email}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/active_tasks')
def get_active_tasks():
    tasks_data = []
    for task_id, task in active_tasks.items():
        tasks_data.append({
            'task_id': task_id,
            'platform': task.platform,
            'status': task.status,
            'created_at': task.created_at.isoformat()
        })

    return jsonify(tasks_data)


@app.route('/completed_tasks')
def get_completed_tasks():
    tasks_data = []
    for task_id, task in completed_tasks.items():
        tasks_data.append({
            'task_id': task_id,
            'platform': task.platform,
            'status': task.status,
            'created_at': task.created_at.isoformat(),
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        })

    return jsonify(tasks_data)


def run_scraper(task):
    """Run the actual scraping process"""
    try:


        # Run appropriate scraper
        if task.platform == "Facebook":
            csv_path = run_facebook_scraper(task.input_value, task.scrolls, task.task_id)
        elif task.platform == "Instagram":
            csv_path = run_instagram_scraper(task.input_value, task.scrolls, task.task_id)
        elif task.platform == "X":
            csv_path = run_x_scraper(task.input_value, task.scrolls, task.task_id)
        else:
            raise ValueError(f"Unknown platform: {task.platform}")

        task.status = 'waiting_for_manual_action'

        # Wait for manual action completion
        flag_file = f"flag_{task.task_id}.txt"
        while True:
            if os.path.exists(flag_file):
                with open(flag_file, "r") as f:
                    if f.read().strip() == "done":
                        break
            time.sleep(1)

        # Update task status
        task.status = 'running'


        # Update task with results
        task.csv_path = csv_path
        task.status = 'completed'
        task.completed_at = datetime.now()

        # Move from active to completed
        active_tasks.pop(task.task_id, None)
        completed_tasks[task.task_id] = task

        # Clean up flag file
        if os.path.exists(flag_file):
            os.remove(flag_file)

    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = datetime.now()

        # Move from active to completed even if failed
        active_tasks.pop(task.task_id, None)
        completed_tasks[task.task_id] = task

        # Clean up flag file
        flag_file = f"flag_{task.task_id}.txt"
        if os.path.exists(flag_file):
            os.remove(flag_file)


def send_csv_email(csv_path, recipient_email, platform):
    """Send CSV file via email using SendGrid"""
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
    import base64

    # Your SendGrid configuration
    SENDGRID_API_KEY =''
    SENDER_EMAIL = ''

    message = Mail(
        from_email=Email(SENDER_EMAIL),
        to_emails=To(recipient_email),
        subject=f"{platform} Scraping Results",
        plain_text_content=Content("text/plain", f"Attached is the CSV file from your {platform} scraping task.")
    )

    # Attach the CSV file
    with open(csv_path, 'rb') as f:
        data = f.read()
        encoded_file = base64.b64encode(data).decode()

    attachment = Attachment()
    attachment.file_content = FileContent(encoded_file)
    attachment.file_type = FileType('text/csv')
    attachment.file_name = FileName(os.path.basename(csv_path))
    attachment.disposition = Disposition('attachment')
    message.attachment = attachment

    # Send email
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"✅ Email sent! Status code: {response.status_code}")

#
# if __name__ == '__main__':
#     # Create templates directory if it doesn't exist
#     os.makedirs('templates', exist_ok=True)
#
#     app.run(debug=True, host='0.0.0.0', port=5000)

import os

# ... your other imports

# Your existing code...

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs(name='templates', exist_ok=True)

    # Get port from environment variable (Railway sets this automatically)
    port = int(os.environ.get('PORT', 5000))

    # Run the app (disable debug for production)
    app.run(debug=False, host='0.0.0.0', port=port)