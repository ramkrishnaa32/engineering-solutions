import constants
import functions
from datetime import datetime
import os

def main():
    # Take MongoDB dump and stored temp folder
    functions.take_mongo_dump(constants.DATABASE_NAME, constants.DUMP_DIR)

    # Create a timestamped folder in S3 for the dump
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    s3_folder = f"{constants.S3_FOLDER}/{constants.DATABASE_NAME}/{timestamp}"

    # Upload all files from the dump directory to S3
    for root, dirs, files in os.walk(constants.DUMP_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            # Create the S3 key by constructing the path without the database name in the second occurrence
            relative_path = os.path.relpath(file_path, constants.DUMP_DIR)
            # Adjust the S3 key to remove the database name from the relative path
            s3_key = os.path.join(s3_folder, relative_path.replace(f"{constants.DATABASE_NAME}/", ""))
            # Upload the file to S3
            functions.upload_to_s3(file_path, constants.S3_BUCKET_NAME, s3_key)

    # Cleanup the local dump directory if needed
    functions.cleanup_dump_directory()

    print(f'Job completed successfully')

if __name__ == "__main__":
    main()