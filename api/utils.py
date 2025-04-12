import os

def split_file(filepath, chunk_size=1.9 * 1024 * 1024 * 1024):
    parts = []
    i = 1
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(int(chunk_size))
            if not chunk:
                break
            part_filename = f"{filepath}_part{i}"
            with open(part_filename, 'wb') as part:
                part.write(chunk)
            parts.append(part_filename)
            i += 1
    return parts

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f}{unit}"
        size /= 1024
    return f"{size:.2f}TB"