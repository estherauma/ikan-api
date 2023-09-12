import random
import string

# Define the characters to choose from
characters = string.ascii_uppercase + string.digits

# Generate an 8-character random string
random_string = ''.join(random.choice(characters) for _ in range(8))

def get_access_code():
    return random_string
