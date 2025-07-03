import logging

a = {}
try:
    a[5]
except KeyError as e:
    raise e  # Noncompliant

try:
    a[5]
except KeyError:
    raise  # Noncompliant

try:
    a[5]
except:
    raise  # Noncompliant

try:
    a[5]
except:
    logging.exception('error while accessing the dict')
    raise

try:
    a[5]
except KeyError:
    logging.exception('error while accessing the dict')
    raise

try:
    a[5]
except KeyError as e:
    logging.exception('error while accessing the dict')
    raise
