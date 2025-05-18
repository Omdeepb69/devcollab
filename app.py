from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Optional
import os
import logging
import json
from datetime import datetime

from config import Config
from utils import Messenger, GitHubIntegration, TaskScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize utilities
messenger = Messenger(browser_path=app.config.get('BROWSER_PATH'))
task_scheduler = TaskScheduler()

# Initialize GitHub integration if token is available
github_integration = None
if app.config.get('GITHUB_TOKEN'):
    github_integration = GitHubIntegration(app.config.get('GITHUB_TOKEN'))
else:
    logger.warning("GitHub token not found. GitHub integration will be disabled.")

# Define forms
class MessageForm(FlaskForm):
    """Form for sending messages"""
    recipient = StringField('Recipient Phone Number', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    delay = IntegerField('Delay (minutes)', default=2, validators=[Optional()])
    submit = SubmitField('Send Message')

class BulkMessageForm(FlaskForm):
    """Form for sending bulk messages"""
    recipients = TextAreaField('Recipients (one per line)', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    interval = IntegerField('Interval between messages (minutes)', default=2, validators=[Optional()])
    submit = SubmitField('Send Bulk Messages')

class GitHubIssueForm(FlaskForm):
    """Form for creating GitHub issues"""
    repository = StringField('Repository', validators=[DataRequired()])
    title = StringField('Issue Title', validators=[DataRequired()])
    body = TextAreaField('Issue Description', validators=[DataRequired()])
    assignees = StringField('Assignees (comma-separated)', validators=[Optional()])
    labels = StringField('Labels (comma-separated)', validators=[Optional()])
    notify = BooleanField('Notify Collaborators via WhatsApp', default=False)
    submit = SubmitField('Create Issue')

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('dashboard.html')

@app.route('/messaging', methods=['GET', 'POST'])
def messaging():
    """Message sending page"""
    form = MessageForm()
    bulk_form = BulkMessageForm()
    
    if form.validate_on_submit():
        result = messenger.send_whatsapp_message(
            form.recipient.data,
            form.message.data,
            delay=form.delay.data
        )
        
        if result['status'] == 'success':
            flash(f"Message scheduled: {result['message']}", 'success')
        else:
            flash(f"Error: {result['message']}", 'danger')
        
        return redirect(url_for('messaging'))
    
    if bulk_form.validate_on_submit():
        recipients = [line.strip() for line in bulk_form.recipients.data.split('\n') if line.strip()]
        
        result = messenger.send_bulk_messages(
            recipients,
            bulk_form.message.data,
            interval_minutes=bulk_form.interval.data
        )
        
        if result['status'] == 'completed':
            flash(f"Bulk messages scheduled for {len(recipients)} recipients", 'success')
        else:
            flash("Error scheduling bulk messages", 'danger')
        
        return redirect(url_for('messaging'))
    
    return render_template('messaging.html', form=form, bulk_form=bulk_form)

@app.route('/github', methods=['GET'])
def github():
    """GitHub repositories page"""
    repositories = []
    
    if github_integration:
        repositories = github_integration.get_repositories(include_private=True)
    else:
        flash("GitHub integration is not configured. Add your GitHub token in the configuration.", 'warning')
    
    return render_template('github_repos.html', repositories=repositories)

@app.route('/github/repo/<repo_name>', methods=['GET'])
def github_repo(repo_name):
    """GitHub repository details page"""
    repo_data = None
    collaborators = []
    commits = []
    
    if github_integration:
        # Get repository details
        repositories = github_integration.get_repositories(include_private=True)
        repo_data = next((repo for repo in repositories if repo['name'] == repo_name), None)
        
        if repo_data:
            # Get collaborators and commits
            collaborators = github_integration.get_collaborators(repo_name)
            commits = github_integration.get_recent_commits(repo_name, count=10)
    else:
        flash("GitHub integration is not configured.", 'warning')
    
    form = GitHubIssueForm()
    form.repository.data = repo_name
    
    return render_template(
        'github_repo.html', 
        repo=repo_data, 
        collaborators=collaborators, 
        commits=commits, 
        form=form
    )

@app.route('/github/create_issue', methods=['POST'])
def create_github_issue():
    """Create a GitHub issue"""
    form = GitHubIssueForm()
    
    if form.validate_on_submit() and github_integration:
        # Process assignees and labels
        assignees = [a.strip() for a in form.assignees.data.split(',') if a.strip()]
        labels = [l.strip() for l in form.labels.data.split(',') if l.strip()]
        
        # Create the issue
        result = github_integration.create_issue(
            form.repository.data,
            form.title.data,
            form.body.data,
            assignees=assignees,
            labels=labels
        )
        
        if result['status'] == 'success':
            flash(f"Issue created: #{result['issue']['number']}", 'success')
            
            # Notify collaborators if requested
            if form.notify.data:
                collaborators = github_integration.get_collaborators(form.repository.data)
                
                for collaborator in collaborators:
                    # Skip if email is not available
                    if not collaborator.get('email'):
                        continue
                    
                    # Build notification message
                    message = f"""
Hello {collaborator.get('name', collaborator['login'])},

A new issue has been created in {form.repository.data}:

Title: {form.title.data}
URL: {result['issue']['url']}

Description:
{form.body.data}

This is an automated notification from DevCollab.
                    """
                    
                    # Schedule notification (using email as identifier instead of phone number in this example)
                    # In a real implementation, you would need to map GitHub usernames to phone numbers
                    logger.info(f"Would notify {collaborator['login']} about new issue")
        else:
            flash(f"Error creating issue: {result['message']}", 'danger')
    else:
        flash("Invalid form submission or GitHub integration not configured", 'danger')
    
    return redirect(url_for('github_repo', repo_name=form.repository.data))

@app.route('/api/pending_tasks', methods=['GET'])
def api_pending_tasks():
    """API endpoint to get pending tasks"""
    result = task_scheduler.get_pending_tasks()
    return jsonify(result)

@app.route('/api/cancel_task/<job_id>', methods=['POST'])
def api_cancel_task(job_id):
    """API endpoint to cancel a scheduled task"""
    result = task_scheduler.cancel_task(job_id)
    return jsonify(result)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Clean up resources when the app is terminated
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    task_scheduler.shutdown()

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)