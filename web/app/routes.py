from app import app, db, queue_client
from datetime import datetime
from app.models import Attendee, Conference, Notification
from flask import render_template, session, request, redirect, url_for, flash, make_response, session
from azure.servicebus.aio import Message
from functools import wraps
import logging
import asyncio
import redis


def async_decor(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapped


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/Registration', methods=['POST', 'GET'])
def registration():
    r = redis.StrictRedis(host=app.config.get('REDIS_HOST'), port=6380,
                          password=app.config.get('REDIS_PASS'), ssl=True)
    r_test = r.ping()
    if request.method == 'POST':
        attendee = Attendee()
        attendee.first_name = request.form['first_name']
        attendee.last_name = request.form['last_name']
        attendee.email = request.form['email']
        attendee.job_position = request.form['job_position']
        attendee.company = request.form['company']
        attendee.city = request.form['city']
        attendee.state = request.form['state']
        attendee.interests = request.form['interest']
        attendee.comments = request.form['message']
        attendee.conference_id = app.config.get('CONFERENCE_ID')

        try:
            db.session.add(attendee)
            db.session.commit()
            if not r_test:
                session['message'] = 'Thank you, {} {}, for registering!'.format(
                    attendee.first_name, attendee.last_name)
            else:
                r.set('message', 'Thank you, {} {}, for registering!'.format(
                    attendee.first_name, attendee.last_name))
            return redirect('/Registration')
        except:
            logging.error('Error occured while saving your information')

    else:
        if not r_test and 'message' in session:
            message = session['message']
            session.pop('message', None)
            return render_template('registration.html', message=message)
        elif r_test:
            message = r.get('message')
            return render_template('registration.html', message=message)
        else:
            return render_template('registration.html')


@app.route('/Attendees')
def attendees():
    attendees = Attendee.query.order_by(Attendee.submitted_date).all()
    return render_template('attendees.html', attendees=attendees)


@app.route('/Notifications')
def notifications():
    notifications = Notification.query.order_by(Notification.id).all()
    return render_template('notifications.html', notifications=notifications)


@app.route('/Notification', methods=['POST', 'GET'])
@async_decor
async def notification():
    if request.method == 'POST':
        notification = Notification()
        notification.message = request.form['message']
        notification.subject = request.form['subject']
        notification.status = 'Notifications submitted'
        notification.submitted_date = datetime.utcnow()

        try:
            db.session.add(notification)
            db.session.commit()

            with queue_client.get_sender() as sender:
                message = Message(f'{notification.id}')
                sender.send(message)

            return redirect('/Notifications')
        except Exception as e:
            logging.error('log unable to save notification')

    else:
        return render_template('notification.html')
