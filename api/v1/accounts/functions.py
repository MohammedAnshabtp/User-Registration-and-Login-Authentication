import random
from random import randint

def randomnumber(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


def validate_password(password):
    special_symbols =['$', '@', '#', '%', '!', '*', '?', '&']
    is_valid = True
    message = ""
    response_data = {}

    if len(password) < 8: 
        message = 'Password length should be at least 8!'
        is_valid = False
    elif len(password) > 20:
        message = 'Password length should not be greater than 20!'
        is_valid = False
    elif not any(char.isdigit() for char in password):
        message = 'Password should have at least one numeral'
        is_valid = False
    elif not any(char.isupper() for char in password):
        message = 'Password should have at least one uppercase letter'
        is_valid = False
    elif not any(char.islower() for char in password): 
        message = 'Password should have at least one lowercase letter'
        is_valid = False
    elif not any(char in special_symbols for char in password):
        message = 'Password should have at least one of the symbols ($, @, #, %, !, *, ?, &)'
        is_valid = False

    if is_valid:
        response_data = {
            "status" : True,
            "message" : "Success"
        }
    else:
        response_data = {
            "status" : False,
            "message" : message
        }
    
    return response_data