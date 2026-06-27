import re

with open('app/persistence/mongodb/indexes.py', 'r') as f:
    content = f.read()

content = re.sub(r'collection=(col\.[A-Z_]+)', r'extra={"collection": \1}', content)

with open('app/persistence/mongodb/indexes.py', 'w') as f:
    f.write(content)
