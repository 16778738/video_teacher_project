import random


def create_random_code():
    code = "06d"%random.randint(0,99999)
    return code