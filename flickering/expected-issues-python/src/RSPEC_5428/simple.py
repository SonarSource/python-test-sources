
def generate_value():
    return "default"


mydict = {}
result = "default"
if "missing" in mydict:
    result = mydict["missing"]  # Noncompliant

if "missing" in mydict:
    result = mydict["missing"]  # Noncompliant
else:
    result = "default"

if "missing" in mydict:
    result = mydict["missing"]  # Compliant. No issue is raised as generate_value() might have some side-effect.
else:
    result = generate_value()
