def foo(condition):
    if condition:
        int = 42  # Noncompliant. The time a variable is defined in a local scope
        #^^
        # Primary message: "Rename this variable; it shadows a builtin."
    else:
        int = "a"
        #^^ Secondary message: "Variable also assigned here."
