#!/usr/bin/env python3
"""
Hasan Email Daemon — Automated Email Communication Manager

Manages all automated email workflows for TemuClaude:
- Customer support auto-replies and escalation
- User feedback collection and routing
- Legal notice delivery
- API communications (key generation, usage alerts)
- Email marketing campaigns
- Welcome emails for new users
- Billing receipts
- Security alerts
- Notification digests

This daemon runs as part of Hasan's autonomous system.
It monitors the email queue and triggers based on system events.
"""

import json
import time
import os
import sys
import requests
from datetime import datetime
from pathlib import Path

# Configuration
TEMUCLAUDE_BASE_URL = os.environ.get('TEMUCLAUDE_BASE_URL', 'https://temuclaude.com')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
HEARTBEAT_FILE = '/tmp/temuclaude_daemons/email_daemon_heartbeat.json'
QUEUE_FILE = '/tmp/temuclaude_daemons/email_queue.json'
LOG_FILE = '/tmp/temuclaude_daemons/email_daemon.log'

# Email types
EMAIL_TYPES = {
    'support': 'Customer Support',
    'feedback': 'User Feedback', 
    'legal': 'Legal Notice',
    'api': 'API Communication',
    'marketing': 'Email Marketing',
    'welcome': 'Welcome Email',
    'billing': 'Billing Receipt',
    'security': 'Security Alert',
}

def log(message, level='INFO'):
    """Log to file and console"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    entry = f"{timestamp} {level} Email Daemon — {message}"
    print(entry)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(entry + '\n')

def update_heartbeat(status='alive', extra=None):
    """Update heartbeat file"""
    os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
    data = {
        'pid': os.getpid(),
        'status': status,
        'last_beat': datetime.now().isoformat(),
        'emails_sent': get_stats().get('total_sent', 0),
        'emails_failed': get_stats().get('total_failed', 0),
    }
    if extra:
        data['extra'] = extra
    with open(HEARTBEAT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_stats():
    """Get email statistics"""
    if not os.path.exists(HEARTBEAT_FILE):
        return {'total_sent': 0, 'total_failed': 0}
    try:
        with open(HEARTBEAT_FILE) as f:
            data = json.load(f)
            return {
                'total_sent': data.get('emails_sent', 0),
                'total_failed': data.get('emails_failed', 0),
            }
    except:
        return {'total_sent': 0, 'total_failed': 0}

def send_via_api(endpoint, payload):
    """Send email via TemuClaude API route"""
    url = f"{TEMUCLAUDE_BASE_URL}/api/email/{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=30, headers={
            'Content-Type': 'application/json',
        })
        if response.status_code == 200:
            data = response.json()
            log(f"Email sent via /api/email/{endpoint}: {data.get('id', 'unknown')}")
            return {'success': True, 'id': data.get('id')}
        else:
            error = response.json().get('error', 'Unknown error')
            log(f"Email failed via /api/email/{endpoint}: {error}", 'ERROR')
            return {'success': False, 'error': error}
    except Exception as e:
        log(f"Email API error: {e}", 'ERROR')
        return {'success': False, 'error': str(e)}

def send_welcome(email, name=None):
    """Send welcome email to new user"""
    return send_via_api('welcome', {'email': email, 'name': name})

def send_support_reply(user_email, user_name, message, category='general'):
    """Send customer support email"""
    return send_via_api('support', {
        'name': user_name,
        'email': user_email,
        'message': message,
        'category': category,
    })

def send_feedback(user_email, user_name, rating, feedback):
    """Send user feedback email"""
    return send_via_api('feedback', {
        'name': user_name,
        'email': user_email,
        'rating': rating,
        'feedback': feedback,
    })

def send_legal_notice(to, subject, content):
    """Send legal notice email"""
    master_key = os.environ.get('TEMUCLAUDE_MASTER_KEY', '')
    url = f"{TEMUCLAUDE_BASE_URL}/api/email/legal"
    try:
        response = requests.post(url, json={
            'to': to,
            'subject': subject,
            'content': content,
        }, timeout=30, headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {master_key}',
        })
        if response.status_code == 200:
            return {'success': True, 'id': response.json().get('id')}
        return {'success': False, 'error': response.json().get('error')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def send_api_notice(to, subject, content, action='notification'):
    """Send API communication email"""
    return send_via_api('api-notice', {
        'to': to,
        'subject': subject,
        'content': content,
        'action': action,
    })

def send_marketing(to, subject, content):
    """Send marketing email"""
    return send_via_api('marketing', {
        'to': to,
        'subject': subject,
        'content': content,
    })

def send_billing(to, subject, amount, plan, period, receipt_id):
    """Send billing receipt email"""
    return send_via_api('billing', {
        'to': to,
        'subject': subject,
        'amount': amount,
        'plan': plan,
        'period': period,
        'receiptId': receipt_id,
    })

def send_security_alert(to, alert_type, message):
    """Send security alert email"""
    return send_via_api('security', {
        'to': to,
        'alertType': alert_type,
        'message': message,
    })

def process_queue():
    """Process pending emails in the queue"""
    if not os.path.exists(QUEUE_FILE):
        return
    
    try:
        with open(QUEUE_FILE) as f:
            queue = json.load(f)
    except:
        return
    
    if not queue.get('pending'):
        return
    
    pending = queue['pending']
    processed = []
    
    for item in pending:
        email_type = item.get('type')
        if email_type == 'welcome':
            result = send_welcome(item.get('email'), item.get('name'))
        elif email_type == 'support':
            result = send_support_reply(item.get('email'), item.get('name'), item.get('message'), item.get('category'))
        elif email_type == 'feedback':
            result = send_feedback(item.get('email'), item.get('name'), item.get('rating'), item.get('feedback'))
        elif email_type == 'marketing':
            result = send_marketing(item.get('to'), item.get('subject'), item.get('content'))
        elif email_type == 'billing':
            result = send_billing(item.get('to'), item.get('subject'), item.get('amount'), item.get('plan'), item.get('period'), item.get('receiptId'))
        elif email_type == 'security':
            result = send_security_alert(item.get('to'), item.get('alertType'), item.get('message'))
        elif email_type == 'api':
            result = send_api_notice(item.get('to'), item.get('subject'), item.get('content'), item.get('action'))
        elif email_type == 'legal':
            result = send_legal_notice(item.get('to'), item.get('subject'), item.get('content'))
        else:
            log(f"Unknown email type: {email_type}", 'WARN')
            continue
        
        processed.append({**item, 'result': result, 'processed_at': datetime.now().isoformat()})
    
    # Move processed to history
    queue.setdefault('history', []).extend(processed)
    queue['pending'] = []
    
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)
    
    log(f"Processed {len(processed)} emails from queue")

def main_loop():
    """Main daemon loop"""
    log("Email Daemon started")
    update_heartbeat('alive', {'note': 'Hasan Email Manager running'})
    
    cycle = 0
    while True:
        try:
            cycle += 1
            
            # Process email queue
            process_queue()
            
            # Update heartbeat every cycle
            update_heartbeat('alive', {'cycle': cycle})
            
            # Sleep 30 seconds between cycles
            time.sleep(30)
            
        except KeyboardInterrupt:
            log("Email Daemon stopped by user")
            update_heartbeat('stopped')
            break
        except Exception as e:
            log(f"Error in main loop: {e}", 'ERROR')
            update_heartbeat('error', {'error': str(e)})
            time.sleep(60)  # Wait longer on error

if __name__ == '__main__':
    main_loop()