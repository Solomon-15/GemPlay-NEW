#!/usr/bin/env python3
import os
import re
import sys

def has_cyrillic(text):
    """Check if text contains Cyrillic characters."""
    return bool(re.search(r'[а-яё]', text, re.IGNORECASE))

def clean_russian_comments(file_path):
    """Remove Russian comments from JavaScript files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Check for single-line comments
            comment_match = re.match(r'^(\s*)//(.*)', line)
            if comment_match:
                indent, comment_text = comment_match.groups()
                if has_cyrillic(comment_text):
                    # Skip Russian comments
                    continue
            
            # Check for block comments (simple case - single line)
            block_comment_match = re.match(r'^(\s*)/\*(.*)\*/\s*$', line)
            if block_comment_match:
                indent, comment_text = block_comment_match.groups()
                if has_cyrillic(comment_text):
                    # Skip Russian block comments
                    continue
            
            cleaned_lines.append(line)
        
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Write back if changed
        if cleaned_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            print(f"Cleaned: {file_path}")
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
                clean_russian_comments(file_path)

if __name__ == '__main__':
    main()