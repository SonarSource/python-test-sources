class Person:
    pass

def get_title(person):
    return "Mr. " if person.gender == Person.MALE else "Mrs. " if person.is_married() else "Miss "  # Noncompliant

def get_title(person):
    if person.gender == Person.MALE:
        return "Mr. "
    return "Mrs. " if person.is_married() else "Miss "

def ignore_comprehension(person):
    return [a if a > 0 else 1 if a < -5 else 2 for a in range(10)] # False Positive


def ignore_comprehension(person):
    return [a if a > 0 else 1 for a in range(10)] if person else None # Compliant
