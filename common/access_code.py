import random
import string
from datetime import datetime

# Define the characters to choose from
characters = string.ascii_uppercase + string.digits

# Generate an 8-character random string
random_string = ''.join(random.choice(characters) for _ in range(8))
timestamp_digits = str(int(datetime.now().timestamp() * 1000))[-3:]
final_access_code = timestamp_digits + random_string

def get_access_code():
    return final_access_code
