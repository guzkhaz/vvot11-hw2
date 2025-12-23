from slugify import slugify

def normalize_filename(text):
    return slugify(
        text,
        lowercase=True,
        separator='-',
        max_length=100
    ) or "document"