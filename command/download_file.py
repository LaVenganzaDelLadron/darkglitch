from command.upload_file import download_file as download_transfer


def download_file(target, path, local_path=None):
    return download_transfer(target, path, local_path)