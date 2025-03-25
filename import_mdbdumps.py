import os
from datetime import datetime
import functions
import constants

def main():

    # Fetching the lastest dump folder from s3
    latest_folder = functions.get_latest_folder(constants.S3_BUCKET_NAME)
    print(f"Latest folder: {latest_folder}")

    # Dowloading the dumps tmp folder
    functions.download_latest_dumps(constants.S3_BUCKET_NAME, latest_folder)
    print(f"Dumps downloaded to {constants.DUMP_DIR}")

    # Importing dumps to mangodb
    functions.import_dumps_to_mongodb(constants.DUMP_DIR)
    print("Dumps imported to MongoDB.")

    # Cleanup the local dump directory if needed
    functions.cleanup_dump_directory()
    
    print(f'Job completed successfully')

if __name__ == "__main__":
    main()