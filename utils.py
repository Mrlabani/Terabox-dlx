import os

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return "%.1f %s" % (size, unit)
        size /= 1024.0
    return "%.1f TB" % (size)

def split_file(file_path, part_size=1024 * 1024 * 1024 * 2):  # 2GB
    parts = []
    base = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        i = 1
        while True:
            chunk = f.read(part_size)
            if not chunk:
                break
            part_path = f"{file_path}.part{i}"
            with open(part_path, 'wb') as part:
                part.write(chunk)
            parts.append(part_path)
            i += 1
    return parts
  
