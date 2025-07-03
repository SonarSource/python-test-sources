#
# Ignore Hex colors
#
a = "#111111"
b = "#111111"
c = "#111111"  # Ok

#
# Ignore encodings
#
a = "utf-8"
b = "utf-8"
c = "utf-8"

def run():
    prepare("this is a duplicate")  # Noncompliant - "action1" is duplicated 3 times
    execute("this is a duplicate")
    release("this is a duplicate")


ACTION_1 = "action1"

def run():
    prepare(ACTION_1)
    execute(ACTION_1)
    release(ACTION_1)

@app.route("/api/users/", methods=['GET', 'POST', 'PUT', 'this is compliant'])
def users():
    pass

@app.route("/api/projects/", methods=['GET', 'POST', 'PUT', 'this is compliant'])  # Compliant
def projects():
    pass

@app.route("/api/products/", methods=['GET', 'POST', 'PUT', 'this is compliant'])  # Compliant
def projects():
    pass