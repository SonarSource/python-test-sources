try:
    raise TypeError()
except ValueError or TypeError:  # Noncompliant
    print("Catching only ValueError")
except ValueError and TypeError:  # Noncompliant
    print("catching only TypeError")
except ValueError or TypeError:  # Noncompliant
    print("Catching only ValueError")
except (ValueError or TypeError) as exc:  # Noncompliant
    print("Catching only ValueError")