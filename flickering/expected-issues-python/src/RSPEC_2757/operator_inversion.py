target = -5
num = 3

target =- num  # Noncompliant; target = -3. Is that really what's meant?
target =+ num  # Noncompliant; target = 3


target = -5
num = 3

target = -num  # Compliant; intent to assign inverse value of num is clear
target += num
