import os

from mofi import Mofi, Donation
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema


mail_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=os.getenv("MAIL_PORT"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)

fm = FastMail(mail_config)
app = Mofi("token")


async def send_email(to: str, subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[to],
        body=body,
        subtype="html",
    )
    await fm.send_message(message)


@app.callback("donation")
async def donation_callback(data: Donation):
    await send_email(
        data.email,
        "Thank you!",
        f"Hello! Thank you for donating {data.amount}{data.currency}!",
    )


app.run()
