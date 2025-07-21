#!/usr/bin/env python3
"""
Quick script to fix CLI integration test patterns.
"""

def fix_cli_integration_tests():
    file_path = "tests/integration/test_cli_integration.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace patterns
    replacements = [
        ('cli_runner.invoke(cli,', 'self.runner.invoke(app,'),
        ('cli_runner,', ''),
        ('migrate-board', 'generate-board'),
        ('--board-name', ''),  # Remove board-name parameter
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Add board name arguments where missing
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "'generate-board'," in line and i + 1 < len(lines):
            # Look at next few lines to see if we need to add board name
            next_line = lines[i + 1]
            if not any(arg in next_line for arg in ["'", '"']):  # No string argument following
                new_lines.append(line)
                new_lines.append("            'test_board',  # Board name")
                i += 1
                continue
        new_lines.append(line)
        i += 1
    
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("Fixed CLI integration tests")

if __name__ == "__main__":
    fix_cli_integration_tests()
