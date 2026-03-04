import os
from dotenv import load_dotenv
from urllib.parse import quote
from utils.airtable_throttler import AirtableThrottler

load_dotenv()
airtable_requester = AirtableThrottler()

def get_user(rec_id):
    print("Retrieving workers from Airtable")
    try:
        response = airtable_requester.throttled_get(
            url=f'https://api.airtable.com/v0/appfccXiah8EtMfbZ/tblU2uvcUVqERiRzv/{rec_id}',
            headers = {
                "Authorization": "Bearer " + os.getenv('AIRTABLE_API_KEY'),
                "Content-Type": "application/json",
            }
        )
        response_data = response.json()
        records = response_data.get('fields', [])
    except Exception as e:
        print(f"Error retrieving Airtable records: {e}")
        records = []
    return records

def get_user_by(field="Record ID", value=None):
    print(f"Retrieving user by {field}: {value}")
    try:
        url = f'https://api.airtable.com/v0/appVBupdRP0pwHBjh/tblMrivRZBk0ZAJbK'
        response = airtable_requester.throttled_get(
            url=url,
            headers = {
                "Authorization": "Bearer " + os.getenv('AIRTABLE_API_KEY'),
                "Content-Type": "application/json",
            },
            params={
                "filterByFormula": f'FIND("{value}", {{{field}}})'
            }
        )
        response_data = response.json()
        record_id = response_data.get('records', [{}])[0].get('id', None)
        print(record_id)
    except Exception as e:
        print(f"Error retrieving Airtable records: {e}")
        record_id = None
    return record_id

def get_kpi_checklist_fields(position):
    print(f"Retrieving KPI checklist fields for position: {position}")
    try:
        url = f'https://api.airtable.com/v0/appVBupdRP0pwHBjh/tblsEjOXdMsKdFNaW?filterByFormula=' + quote(f'FIND("{position}", {{Position Title}})')
        print(url)
        response = airtable_requester.throttled_get(
            url=url,
            headers = {
                "Authorization": "Bearer " + os.getenv('AIRTABLE_API_KEY'),
                "Content-Type": "application/json",
            }
        )
        response_data = response.json()
        records = response_data.get('records', [])
        
        form_schema = []
        for record in records:
            fields = record.get('fields', {})
            record_id = record.get('id')
            kpi_name = fields.get('KPI Description')
            expectation = fields.get('Expectations')
            is_required = fields.get('Is Required', False)
            if kpi_name:
                form_schema.append({
                    "name": record_id,
                    "description": kpi_name,
                    "expectation": expectation,
                    "isRequired": is_required
                })
        final_schema = {
        "section": "KPI Checklist",
        "fields": form_schema
        }

    except Exception as e:
        print(f"Error retrieving KPI checklist fields: {e}")
        final_schema = {
            "section": "KPI Checklist",
            "fields": []
        }
    return final_schema


def submit_data_to_airtable(data):
    print("Submitting data to Airtable")

    try:
        response = airtable_requester.throttled_post(
            url='https://api.airtable.com/v0/appVBupdRP0pwHBjh/tblQyRrzoGOVLve2a',
            headers = {
                "Authorization": "Bearer " + os.getenv('AIRTABLE_API_KEY'),
                "Content-Type": "application/json",
            },
            json={
                "fields": {
                    "scorecard_proctor": [get_user_by(field="Record ID", value=data.get("scorecard_proctor_fieldset", {}).get("record_id", ""))],
                    "employee": [get_user_by(field="Record ID", value=data.get("recordId", {}))],
                    "position": data.get("employee_being_scored_fieldset", {}).get("position", "")
                }
            }
        )
        if response.status_code == 200:
            print("Data submitted successfully")
            return True
        else:
            print(f"Failed to submit data: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error submitting data to Airtable: {e}")
        return False