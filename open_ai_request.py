import os
from openai import OpenAI

# Load sensitive information from environment variables
apiKey = os.getenv('OPENAI_API_KEY')
orgId = os.getenv('OPENAI_ORG_ID')
projectId = os.getenv('OPENAI_PROJECT_ID')

if not apiKey or not orgId or not projectId:
    raise ValueError("API key, Organization ID, and Project ID must be set in environment variables.")

# Initialize OpenAI
client = OpenAI(
    api_key=apiKey,
    organization=orgId,
    project=projectId
)

try:
    # Create a completion
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "write a haiku about ai"}
        ]
    )
    print(f"openAI response: {completion}")
except Exception as e:
    error_message = str(e)
    if "insufficient_quota" in error_message:
        print(f"You have exceeded your current quota. Please check your plan and billing details.\nerror_message: \n{error_message}")
    else:
        print(f"An error occurred: {e}")