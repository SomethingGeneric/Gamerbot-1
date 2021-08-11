import os

from util_functions import syslog


class VoiceState:
    def __init__(self):
        syslog.log("Sound-State", "Initalized")
        if os.path.exists(".voice_state"):
            os.remove(".voice_state")
        with open(".voice_state", "w") as f:
            f.write("0")
        return

    def check_state(self):
        with open(".voice_state") as f:
            state = f.read()
        syslog.log("Sound-State", "State queried. Result: " + state)
        if state == "0":  # failsafe
            return False
        else:
            return True

    def set_state(self, new):
        syslog.log("Sound-State", "State set to " + new)
        os.remove(".voice_state")
        with open(".voice_state", "w") as f:
            f.write(new)
