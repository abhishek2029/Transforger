"""
One-time setup script to create BDA Blueprint and Project.
Run this once before starting the app.
"""
import boto3
import json
import time
import os

REGION = os.environ.get("AWS_REGION", "us-east-1")

bda = boto3.client("bedrock-data-automation", region_name=REGION)

BLUEPRINT_SCHEMA = {
    "class": "PharmacyPrescription",
    "description": "Blueprint for extracting structured data from pharmacy prescription dispensing records. Handles multi-page documents where each page is a separate prescription.",
    "properties": {
        "pharmacy_name": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The name of the pharmacy"
        },
        "pharmacy_address": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The full address of the pharmacy"
        },
        "pharmacy_phone": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The phone number of the pharmacy"
        },
        "pharmacy_license": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The pharmacy license number"
        },
        "date_dispensed": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The date the prescription was dispensed"
        },
        "rx_number": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The prescription RX number"
        },
        "pharmacist_name": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The name of the dispensing pharmacist"
        },
        "pharmacy_technician": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The name of the pharmacy technician"
        },
        "patient_name": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The full name of the patient"
        },
        "patient_dob": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The patient date of birth"
        },
        "patient_id": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The patient ID number"
        },
        "patient_address": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The patient full address"
        },
        "patient_phone": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The patient phone number"
        },
        "patient_allergies": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "Known allergies, comma separated"
        },
        "insurance_provider": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The insurance company name only, without member ID"
        },
        "insurance_member_id": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The insurance member ID number"
        },
        "physician_name": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The prescribing physician full name with title"
        },
        "physician_specialty": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The physician medical specialty"
        },
        "clinic_name": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The name of the prescribing clinic or practice"
        },
        "clinic_address": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The address of the prescribing clinic"
        },
        "npi_number": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The physician NPI number"
        },
        "dea_number": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The physician DEA number"
        },
        "physician_phone": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The physician contact phone number"
        },
        "drug_generic_name": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The generic drug name"
        },
        "drug_brand_name": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The brand name of the drug"
        },
        "drug_strength": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The drug strength with unit"
        },
        "dosage_form": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The dosage form e.g. Tablet, Capsule"
        },
        "ndc_number": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The NDC number of the drug"
        },
        "quantity_dispensed": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The quantity dispensed with unit e.g. 60 tablets"
        },
        "days_supply": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The days supply e.g. 30 days"
        },
        "refills_remaining": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "Refills remaining formatted as X of Y authorized"
        },
        "lot_number": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The drug lot number"
        },
        "expiration_date": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The drug expiration date"
        },
        "sig_directions": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The full SIG directions for use text"
        },
        "warnings": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "All warnings and counseling notes as a semicolon-separated list, without emoji symbols"
        },
        "retail_price": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The retail price with dollar sign"
        },
        "insurance_covered": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The amount covered by insurance with dollar sign"
        },
        "patient_copay": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The patient copay amount with dollar sign"
        },
        "payment_method": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The payment method, simplified to card type and last 4 digits"
        },
        "patient_counseled": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "Whether patient was counseled: Yes or No"
        },
        "rph_initials": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The pharmacist initials"
        },
        "verification_time": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The time of verification"
        },
        "next_refill_date": {
            "type": "string",
            "inferenceType": "explicit",
            "instruction": "The next refill eligible date"
        }
    }
}


def setup():
    print("Creating BDA Blueprint...")
    bp_resp = bda.create_blueprint(
        blueprintName="pharmacy-prescription-extractor",
        type="DOCUMENT",
        blueprintStage="LIVE",
        schema=json.dumps(BLUEPRINT_SCHEMA)
    )
    blueprint_arn = bp_resp["blueprint"]["blueprintArn"]
    print(f"Blueprint ARN: {blueprint_arn}")

    print("Creating BDA Project...")
    proj_resp = bda.create_data_automation_project(
        projectName="doc-transformer-project",
        projectStage="LIVE",
        standardOutputConfiguration={
            "document": {
                "extraction": {
                    "granularity": {"types": ["DOCUMENT", "PAGE"]},
                    "boundingBox": {"state": "ENABLED"}
                },
                "generativeField": {
                    "state": "ENABLED"
                },
                "outputFormat": {
                    "textFormat": {"types": ["PLAIN_TEXT"]},
                    "additionalFileFormat": {"state": "DISABLED"}
                }
            }
        },
        customOutputConfiguration={
            "blueprints": [
                {
                    "blueprintArn": blueprint_arn,
                    "blueprintVersion": "1",
                    "blueprintStage": "LIVE"
                }
            ]
        }
    )
    project_arn = proj_resp["projectArn"]
    print(f"Project ARN: {project_arn}")

    # Wait for project to be ready
    print("Waiting for project to be ready...")
    for _ in range(30):
        status = bda.get_data_automation_project(projectArn=project_arn)
        proj_status = status["project"]["status"]
        print(f"  Status: {proj_status}")
        if proj_status == "COMPLETED":
            break
        time.sleep(2)

    # Save ARNs for the app
    config = {
        "blueprint_arn": blueprint_arn,
        "project_arn": project_arn,
        "region": REGION
    }
    with open("backend/bda_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print(f"\nConfig saved to backend/bda_config.json")
    print("Setup complete!")


if __name__ == "__main__":
    setup()
