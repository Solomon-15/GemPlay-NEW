#!/usr/bin/env python3
import os
import re

def find_unused_imports(file_path):
    """Find and remove unused imports from JavaScript files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Find import lines
        import_lines = []
        other_lines = []
        
        for i, line in enumerate(lines):
            if re.match(r'^\s*import\s+', line):
                import_lines.append((i, line))
            else:
                other_lines.append(line)
        
        # Join non-import content
        rest_of_file = '\n'.join(other_lines)
        
        # Check which imports are actually used
        used_imports = []
        
        for line_num, import_line in import_lines:
            # Extract imported names
            # Handle different import patterns
            if 'from' in import_line:
                # import { A, B } from 'module' or import A from 'module'
                match = re.search(r'import\s+({[^}]*}|\w+)\s+from', import_line)
                if match:
                    import_part = match.group(1)
                    if import_part.startswith('{') and import_part.endswith('}'):
                        # Named imports
                        names = re.findall(r'\w+', import_part)
                        used = any(re.search(r'\b' + name + r'\b', rest_of_file) for name in names)
                    else:
                        # Default import
                        used = re.search(r'\b' + import_part + r'\b', rest_of_file) is not None
                else:
                    used = True  # Keep if we can't parse
            else:
                # import 'module' (side effect)
                used = True
            
            if used:
                used_imports.append(import_line)
        
        # Reconstruct file
        new_lines = used_imports + [''] + other_lines if used_imports else other_lines
        new_content = '\n'.join(new_lines)
        
        # Remove multiple empty lines
        new_content = re.sub(r'\n\n\n+', '\n\n', new_content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Cleaned imports: {file_path}")
            return True
            
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    # Process all JavaScript files in frontend/src
    frontend_src = '/app/frontend/src'
    
    for root, dirs, files in os.walk(frontend_src):
        for file in files:
            if file.endswith('.js'):
                file_path = os.path.join(root, file)
                find_unused_imports(file_path)

if __name__ == '__main__':
    main()