# Prints the time exactly three days from now in UTC

import datetime
import time

now = datetime.datetime.now()
later = now + datetime.timedelta(seconds=time.timezone, days=3)
print later.strftime("%A, %B %d, at %H:%M UTC")
