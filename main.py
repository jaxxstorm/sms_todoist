import logging
import os

from pytodoist import todoist
from twilio.twiml.messaging_response import MessagingResponse


TODOIST_API_KEY = os.environ['TODOIST_API_KEY']
TODOIST_PROJECT = os.environ['TODOIST_PROJECT']

def add_task(request):
    sender = request.values.get('From')
    body = request.values.get('Body')
    
    user = todoist.login_with_api_token(TODOIST_API_KEY)
    project = user.get_project(TODOIST_PROJECT)

    if body.startswith("!!"):
        priority = todoist.Priority.VERY_HIGH
        text = body[2:].lstrip()
    elif body.startswith("!"):
        priority = todoist.Priority.HIGH
        text = body[1:].lstrip()
    else:
        priority = todoist.Priority.LOW
        text = body

    task = project.add_task(text, priority=priority)

    # Respond to confirm
    resp = MessagingResponse()
    resp.message("Thanks, your task has been added to %s" % project.name)

    return str(resp), 200, {'Content-Type': 'application/xml'}
