import os
from datetime import datetime
import functions
import constants
import boto3
import pandas as pd
from io import StringIO
import json

def main():

    # Initialize a session using your AWS credentials
    s3 = boto3.client('s3')
    
    # Read yearly horoscope from S3
    file_key = 'horoscope-dumps/yearly_horoscope.csv'
    response = s3.get_object(Bucket=constants.S3_BUCKET_NAME, Key=file_key)
    content = response['Body'].read().decode('utf-8')

    # Use pandas to read the CSV data
    df = pd.read_csv(StringIO(content))
    print(f'Dataframe length: {len(df)}')
    
    # Convert DataFrame to JSON format
    json_data = df.to_json(orient='records', lines=False)
    data_dict = json.loads(json_data)

    # for x in range(0,len(data_dict)):
    #     print(data_dict[x])
    
    # loading data to mangoDB
    functions.load_json_to_mongodb(data_dict, 'horoscope_yearly')

    print(f'Job completed successfully')

if __name__ == "__main__":
    main()