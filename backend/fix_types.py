import os
import re

for root, dirs, files in os.walk('app'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Replace | with Union/Optional patterns
            content = re.sub(r':\s*(\w+)\s*\|\s*None(?!\w)', r': Optional[\1]', content)
            content = re.sub(r'->\s*(\w+)\s*\|\s*None(?!\w)', r'-> Optional[\1]', content)
            content = re.sub(r':\s*(\w+)\s*\|\s*list\[', r': Union[\1, list[', content)
            content = re.sub(r':\s*tuple\[(\w+),\s*(\w+)\]\s*\|\s*(\w+)', r': Union[tuple[\1, \2], \3]', content)
            
            # Ensure imports
            if 'Optional[' in content or 'Union[' in content:
                if 'from typing import' not in content:
                    if 'from __future__ import annotations' in content:
                        content = content.replace('from __future__ import annotations\n', 'from __future__ import annotations\nfrom typing import Optional, Union\n')
                    else:
                        content = 'from typing import Optional, Union\n' + content
                elif 'Optional' not in content.split('from typing import')[1].split('\n')[0]:
                    content = re.sub(r'from typing import', 'from typing import Optional, Union,', content, count=1)
            
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Fixed: {filepath}")

print("All files fixed!")
