# https://github.com/PyCQA/pylint/issues/1175

for x in [0, 1, 2]:
    if x == 2:
        break
else:
    raise ValueError('Value not found')

print(x) # True Negative, cannot reproduce problem with pylint



def func(li):
    if not li:
        return
    for a in li:
        pass
    print(a)  # False Positive