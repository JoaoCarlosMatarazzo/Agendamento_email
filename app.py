from flask import Flask, render_template, redirect, url_for, flash
from config import Config
from models import db, Event
from forms import EventForm
from flask_mail import Mail, Message
from twilio.rest import Client
import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            email=form.email.data,
            phone_number=form.phone_number.data
        )
        db.session.add(event)
        db.session.commit()
        flash('Event added successfully!')
        return redirect(url_for('index'))
    events = Event.query.all()
    return render_template('index.html', form=form, events=events)

@app.route('/send_reminders')
def send_reminders():
    events = Event.query.filter(Event.date >= datetime.datetime.utcnow(), Event.reminder_sent == False).all()
    for event in events:
        # Send email reminder
        msg = Message('Event Reminder', sender='your-email@gmail.com', recipients=[event.email])
        msg.body = f'Reminder: You have an event titled "{event.title}" scheduled for {event.date}.'
        mail.send(msg)

        # Send SMS reminder if phone number is provided
        if event.phone_number:
            client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
            client.messages.create(
                body=f'Reminder: You have an event titled "{event.title}" scheduled for {event.date}.',
                from_=app.config['TWILIO_PHONE_NUMBER'],
                to=event.phone_number
            )

        event.reminder_sent = True
        db.session.commit()
    flash('Reminders sent successfully!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)


