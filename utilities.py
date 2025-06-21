import csv
from google.cloud import secretmanager
import requests

PROJECT_ID = "central-oregon-action-network"


def access_secrets(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8').rstrip('\n')

def update_secret(secret_id, new_secret_version):
    client = secretmanager.SecretManagerServiceClient()
    parent = client.secret_path(PROJECT_ID, secret_id)
    payload = new_secret_version.encode("UTF-8")

    response = client.add_secret_version(
        request={
            "parent": parent,
            "payload": {
                "data": payload
            }
        }
    )
    print(f"Added secret version: {response.name}")


SERVICES_ENDPOINT = "http://127.0.0.1:8080/api/services"

def fetch_services_and_save_to_csv():
    '''Not used by application, but useful when managing database entries'''
    url = SERVICES_ENDPOINT
    output_file = "services.csv"

    try:
        response = requests.get(url)
        response.raise_for_status()
        services = response.json()

        with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Name", "ID"])  # CSV header

            for service in services:
                name = service.get("name")
                service_id = service.get("id")
                writer.writerow([name, service_id])

        print(f"Saved {len(services)} services to '{output_file}'.")

    except requests.RequestException as e:
        print(f"Error fetching services: {e}")
