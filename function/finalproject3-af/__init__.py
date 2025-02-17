import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import psycopg2.extras


def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info(
        'Python ServiceBus queue trigger processed message: %s', notification_id)

    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"])

    try:
        cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

        # Get notification message and subject from database using the notification_id
        cur.execute(
            f"SELECT * FROM public.notification WHERE public.notification.id = {notification_id}")
        notification = dict(cur.fetchone())

        if notification:
            # Get attendees email and name
            cur.execute(f"SELECT * FROM public.attendee ORDER BY id ASC ")
            attendees = cur.fetchall()

            # Loop through each attendee and send an email with a personalized subject
            count = 0
            for attendee in attendees:
                dict_attendee = dict(attendee)
                subject = '{}: {}'.format(
                    dict_attendee["first_name"], notification["subject"])
                send_email(dict_attendee["email"], subject, notification["message"])
                count += 1

            if count > 0:
                new_status = f"Notified {count} attendees"

                # Update the notification table by setting the completed date and updating the status with the total number of attendees notified
                update_notification_query = f"UPDATE public.notification SET status = '{new_status}', completed_date = '{datetime.utcnow()}' WHERE public.notification.id = {notification_id}"
                cur.execute(update_notification_query)
                conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        if conn:
            cur.close()
            conn.close()


def send_email(email, subject, body):
    SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
    if not SENDGRID_API_KEY:
        message = Mail(
            from_email=os.environ["ADMIN_EMAIL_ADDRESS"],
            to_emails=email,
            subject=subject,
            plain_text_content=body)
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
        except Exception as e:
            logging.error(e.message)
