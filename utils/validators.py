"""Input validation helpers."""


def allowed_file(filename, allowed_extensions):
    """True if `filename` has an extension in `allowed_extensions` (e.g. {'pdf'}).

    This checks the name only. The PDF parser separately checks the file's
    real contents, because a file extension can be faked.
    """
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )
