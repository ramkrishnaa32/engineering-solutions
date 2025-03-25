import constants
import subprocess
import boto3
import json
from datetime import datetime
from pymongo import MongoClient
import os

def get_credentials(secret_name, region_name):
    """
    Fetches MongoDB credentials from AWS Secrets Manager.
    :param secret_name: Name of the secret in AWS Secrets Manager.
    :param region_name: AWS region where the secret is stored.
    :return: MDB_USER, MDB_PASS (MongoDB username and password).
    """
    # Create a Secrets Manager client
    client = boto3.client('secretsmanager', region_name)
    try:
        # Fetch the secret value from AWS Secrets Manager
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        # Parse the secret string as JSON
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        # Retrieve MongoDB credentials
        MDB_USER = secret_dict['astrotech-dev-rw-mdb-user']
        MDB_PASS = secret_dict['astrotech-dev-rw-mdb-pass']
        return MDB_USER, MDB_PASS
    except Exception as e:
        print(f"Error fetching credentials: {e}")
        return None, None

def take_mongo_dump(DATABASE_NAME, DUMP_DIR):
    # Fetching credentials from secretsmanager
    secret_name = 'astrotech-dev-mdb-secrets'
    region_name = 'ap-south-1'
    MDB_USER, MDB_PASS = get_credentials(secret_name, region_name)
    MONGO_URI = f'mongodb+srv://{MDB_USER}:{MDB_PASS}@{constants.MONGO_URL}'
    """Run mongodump command to take a dump of the MongoDB database."""
    dump_command = [
        "mongodump",
        f"--uri={MONGO_URI}",
        f"--db={DATABASE_NAME}",
        f"--out={DUMP_DIR}"
    ]
    try:
        # Running the mongodump command
        subprocess.run(dump_command, check=True)
        print(f"MongoDB dump successfully created at {DUMP_DIR}")
    except subprocess.CalledProcessError as error:
        print(f"Error taking MongoDB dump: {error}")
        exit(1)

def upload_to_s3(file_path, s3_bucket, s3_key):
    """Upload a file to an S3 bucket."""
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_path, s3_bucket, s3_key)
        print(f"Uploaded {file_path} to s3://{s3_bucket}/{s3_key}")
    except Exception as error:
        print(f"Error uploading to S3: {error}")
        exit(1)

def cleanup_dump_directory():
    """Remove the local dump directory to clean up space."""
    try:
        subprocess.run(["rm", "-rf", constants.DUMP_DIR], check=True)
        print(f"Cleaned up local dump directory: {constants.DUMP_DIR}")
    except subprocess.CalledProcessError as error:
        print(f"Error cleaning up dump directory: {error}")

def get_latest_folder(s3_bucket):
    """Get the latest folder from the S3 bucket."""
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix='mongodb-dumps/astrotech/')
    if 'Contents' not in response:
        raise ValueError("No contents found in the specified S3 path.")
    
    folders = []
    for obj in response['Contents']:
        key = obj['Key']
        print(f"Found key: {key}")
        parts = key.split('/')
        print(f'parts: {parts}')
        if len(parts) >= 4:  # Check if there's a valid timestamp folder
            timestamp = parts[2]
            print(f"Checking timestamp: {timestamp}")
            
            try:
                # Try to parse the timestamp to ensure it's valid
                datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S")
                folders.append(timestamp)
                print(f'folders timestamp: {folders}')
            except ValueError:
                print(f"Skipping invalid timestamp: {timestamp}")

    # Get the latest timestamp
    if not folders:
        raise ValueError("No valid timestamp folders found.")
    
    latest_folder = max(folders, key=lambda x: datetime.strptime(x, "%Y-%m-%d_%H-%M-%S"))
    return latest_folder

def download_latest_dumps(s3_bucket, latest_folder):
    """Download the latest dumps from S3."""
    s3 = boto3.resource('s3')
    response = s3.Bucket(s3_bucket).objects.filter(Prefix=f'mongodb-dumps/astrotech/{latest_folder}/')
    
    for obj in response:
        target = os.path.join(constants.DUMP_DIR, os.path.relpath(obj.key, f'mongodb-dumps/astrotech/'))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        s3.Bucket(s3_bucket).download_file(obj.key, target)

def import_dumps_to_mongodb(DUMP_DIR):
    """Import the downloaded dumps into MongoDB."""
    secret_name = 'astrotech-dev-mdb-secrets'
    region_name = 'ap-south-1'
    MDB_USER, MDB_PASS = get_credentials(secret_name, region_name)
    MONGO_URI = f'mongodb+srv://{MDB_USER}:{MDB_PASS}@{constants.MONGO_URL}'
    try:
        # Call mongorestore with the specified URI and dump directory
        subprocess.run(['mongorestore', '--uri', MONGO_URI, DUMP_DIR], check=True)
        print(f"Successfully imported dumps from {DUMP_DIR} to MongoDB.")
    except subprocess.CalledProcessError as error:
        print(f"Error occurred during mongorestore: {error}")


def load_json_to_mongodb(json_data, collection_name):

    # Retrieve MongoDB credentials
    secret_name = 'astrotech-dev-mdb-secrets'
    region_name = 'ap-south-1'
    MDB_USER, MDB_PASS = get_credentials(secret_name, region_name)
    
    # Construct the MongoDB URI
    MONGO_URI = f'mongodb+srv://{MDB_USER}:{MDB_PASS}@{constants.MONGO_URL}'
    client = MongoClient(MONGO_URI)
    
    # Specify the database and collection
    db = client['astrotech']
    collection = db[collection_name]
    
    # Get the current datetime for the 'last_update' field
    last_update_date = datetime.now()

    try:
        # Drop the collection if it exists
        if collection_name in db.list_collection_names():
            print(f"Collection {collection_name} exists. Dropping the collection before loading new data.")
            collection.drop()
            print(f"Collection {collection_name} dropped successfully.")
        
        # Insert the JSON data into the specified collection
        if isinstance(json_data, list):  # Check if the data is a list of records
            result = collection.insert_many(json_data)
            inserted_ids = result.inserted_ids
        else:
            result = collection.insert_one(json_data)
            inserted_ids = [result.inserted_id]

        # Print success message for insert
        print(f"Successfully inserted {len(inserted_ids)} documents into {collection_name} collection.")
        
        # Update the last_update field with the current timestamp for all inserted documents
        collection.update_many(
            {'_id': {'$in': inserted_ids}},  # Match the inserted documents
            {'$set': {'last_updated_date': last_update_date}}  # Set the 'last_updated_date' field
        )
        
        print(f"Last update date set to {last_update_date} for {len(inserted_ids)} documents.")
    
    except Exception as error:
        print(f"Error occurred during MongoDB insert or update: {error}")
    finally:
        client.close()


def load_monthly_horoscope_to_mongodb(json_data, collection_name):

    # Retrieve MongoDB credentials
    secret_name = 'astrotech-dev-mdb-secrets'
    region_name = 'ap-south-1'
    MDB_USER, MDB_PASS = get_credentials(secret_name, region_name)
    
    # Construct the MongoDB URI
    MONGO_URI = f'mongodb+srv://{MDB_USER}:{MDB_PASS}@{constants.MONGO_URL}'
    client = MongoClient(MONGO_URI)
    
    # Specify the database and collection
    db = client['astrotech']
    collection = db[collection_name]
    
    # Get the current datetime for the 'last_update' field
    last_update_date = datetime.now()

    try:
        # # Drop the collection if it exists
        # if collection_name in db.list_collection_names():
        #     print(f"Collection {collection_name} exists. Dropping the collection before loading new data.")
        #     collection.drop()
        #     print(f"Collection {collection_name} dropped successfully.")
        
        # Insert the JSON data into the specified collection
        if isinstance(json_data, list):  # Check if the data is a list of records
            result = collection.insert_many(json_data)
            inserted_ids = result.inserted_ids
        else:
            result = collection.insert_one(json_data)
            inserted_ids = [result.inserted_id]

        # Print success message for insert
        print(f"Successfully inserted {len(inserted_ids)} documents into {collection_name} collection.")
        
        # Update the last_update field with the current timestamp for all inserted documents
        collection.update_many(
            {'_id': {'$in': inserted_ids}},  # Match the inserted documents
            {'$set': {'last_updated_date': last_update_date}}  # Set the 'last_updated_date' field
        )
        
        print(f"Last update date set to {last_update_date} for {len(inserted_ids)} documents.")
    
    except Exception as error:
        print(f"Error occurred during MongoDB insert or update: {error}")
    finally:
        client.close()


def get_astrology_credentials(secret_name, region_name):
    """
    Fetches Astrology API credentials from AWS Secrets Manager.
    :param secret_name: Name of the secret in AWS Secrets Manager.
    :param region_name: AWS region where the secret is stored.
    :return: USER_ID, API_KEY (MongoDB username and password).
    """
    # Create a Secrets Manager client
    client = boto3.client('secretsmanager', region_name)
    try:
        # Fetch the secret value from AWS Secrets Manager
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        # Parse the secret string as JSON
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        # Retrieve MongoDB credentials
        USER_ID = secret_dict['user_id']
        API_KEY = secret_dict['api_key']
        return USER_ID, API_KEY
    except Exception as error:
        print(f"Error fetching credentials: {error}")
        return None, None
    