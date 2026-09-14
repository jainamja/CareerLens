import os
import re

for root, _, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = re.sub(
                r'class="card shadow-sm border-0(.*?)"\s*style="border-radius:\s*12px;"',
                r'class="bento-card\1"',
                content
            )
            new_content = re.sub(
                r'class="card shadow-sm border-0(.*?)"',
                r'class="bento-card\1"',
                new_content
            )
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
