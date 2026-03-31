import io

try:
    with io.open('requirements.txt', 'r', encoding='utf-16le') as f:
        content = f.read()
except UnicodeError:
    with io.open('requirements.txt', 'r', encoding='utf-8') as f:
        content = f.read()

with io.open('requirements.txt', 'w', encoding='utf-8') as f:
    f.write(content.strip() + '\ncustomtkinter\npytest\n')
print("Successfully updated requirements.txt")
