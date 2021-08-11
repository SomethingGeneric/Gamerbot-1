import smtplib, sys


class BotMailer:
    def __init__(self, faddr, passw, toaddr):
        self.faddr = faddr
        self.passw = passw
        self.toaddr = toaddr

    def send(self, subject, text):
        try:
            self.server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            self.server.ehlo()
            self.server.login(self.faddr, self.passw)
        except Exception as e:
            print(str(e))
        message = (
            """"\
From: {{from}}
To: {{to}}
Subject: {{subject}}

{{body}}
        """.replace(
                "{{from}}", self.faddr
            )
            .replace("{{to}}", self.toaddr)
            .replace("{{subject}}", subject)
            .replace("{{body}}", text)
        )
        try:
            self.server.sendmail(self.faddr, self.toaddr, message)
        except Exception as e:
            print(str(e))

    def close(self):
        try:
            self.server.close()
        except Exception as e:
            print(str(e))


if __name__ == "__main__":
    m = BotMailer(
        "mcompton2002@gmail.com",
        open("emailpass.txt").read().strip(),
        "3019745990@vtext.com",
    )
    m.send("Fuck you", str(sys.argv))
