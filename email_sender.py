import smtplib, ssl


def send_email(subject, body):
    port = 465
    sender_email = "crng2121@gmail.com"
    receiver_email = "crng2121@gmail.com"
    password = "jggojtfzyexlitum"
    smtp_server = "smtp.gmail.com"
    message = f"""\
Subject: {subject}

{body}"""

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        print(f"Email successfully sent to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")
