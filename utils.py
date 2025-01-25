def human_readable_size(file_size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if file_size < 1024:
            break
        file_size /= 1024
    return f"{file_size:.2f} {unit}"