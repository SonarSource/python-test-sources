# pylint: disable=pointless-statement,pointless-string-statement

['1' '2']  # Noncompliant
['1' '2', '3']  # Noncompliant
['1', '2' '3']  # Noncompliant
['1', '2' '3', '4']  # Noncompliant

['a', 'b'  # Noncompliant
 'c']


my_string = ('a'  # Ok. Even if it is suspicious (this is not a tuple)
    'b')
# As the rule says: We only raise when the concatenated strings are on the same line
# or they are in a list/tuple/set. This is not the case here.
# Example in a real project: https://github.com/JetBrains/intellij-community/blob/bee33e42508dd066a88a96e1fec0133529eafb35/python/helpers/pydev/pydevd_attach_to_process/winappdbg/breakpoint.py#L1506-L1508


def foo():
    return 'a' 'b'  # Noncompliant. Note: pylint does not raise on this

# Note that the following example isn't a real tuple. But we detect it as a potential tuple.
('1' '2')  # Noncompliant. But maybe this would raise FP. to check on peach. Pylint doesn't raise on this.
('1' '2', '3')  # Noncompliant
('1', '2' '3')  # Noncompliant

{'1' '2'}  # Noncompliant
{'1' '2', '3'}  # Noncompliant
{'1', '2' '3'}  # Noncompliant

print('1', '2' '3')  # Noncompliant. Note: pylint does not raise on function calls

('a', 'b'  # Noncompliant
 'c')

# Ok
('1 \
 2')

# Noncompliant
('1' '2 \
 3')

f'1' '2'  # Ok. f-string and string
F'1' '2'  # Ok. prefixes are case insensitive
F'1' f'2'  # Noncompliant
F'1' fr'2'  # Ok
u'1' '2' # Ok

(u"1" u"2")  # Noncompliant
{r'''1''' r'''2'''}  # Noncompliant
["""1""" """2"""]  # Noncompliant

"1" '2' # Ok
"1" """
2""" # Ok. Even if strange


# Note: Pylint doesn't raise on bytes. Let's check on Peach before adding an exception.
[b'A' b'B']  # Noncompliant.
