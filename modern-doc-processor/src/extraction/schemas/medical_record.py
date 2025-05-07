# src/extraction/schemas/medical_record.py

MEDICAL_RECORD_SCHEMA = {
    "type": "object",
    "properties": {
        "patient": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "patterns": [
                        r"(?:Patient Name|Name)[:.\s]*(.*?)(?:\n|$)",
                        r"(?:Patient)[:.\s]*(.*?)(?:\n|$)"
                    ]
                },
                "id": {
                    "type": "string",
                    "patterns": [
                        r"(?:Patient ID|MRN|Medical Record Number|Chart Number)[:.\s#]*([\w\-]+)"
                    ]
                },
                "dob": {
                    "type": "string",
                    "patterns": [
                        r"(?:DOB|Date of Birth|Born)[:.\s]*([\d\/\-\.]+)",
                        r"(?:DOB|Date of Birth|Born)[:.\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
                    ]
                },
                "gender": {
                    "type": "string",
                    "patterns": [
                        r"(?:Gender|Sex)[:.\s]*(Male|Female|M|F|Other)"
                    ]
                },
                "address": {
                    "type": "string",
                    "patterns": [
                        r"(?:Address|Location|Residence)[:.\s]*(.*?)(?:\n\n|$)"
                    ]
                },
                "phone": {
                    "type": "string",
                    "patterns": [
                        r"(?:Phone|Tel|Contact|Ph)[:.\s]*([\+\(\)\d\s\-\.]{10,})"
                    ]
                }
            }
        },
        "provider": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "patterns": [
                        r"(?:Doctor|Physician|Provider|MD|Dr)[:.\s]*(.*?)(?:\n|$)"
                    ]
                },
                "id": {
                    "type": "string",
                    "patterns": [
                        r"(?:Provider ID|NPI|License)[:.\s#]*([\w\-]+)"
                    ]
                },
                "facility": {
                    "type": "string",
                    "patterns": [
                        r"(?:Facility|Hospital|Clinic|Center)[:.\s]*(.*?)(?:\n|$)"
                    ]
                }
            }
        },
        "encounter": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "patterns": [
                        r"(?:Encounter Date|Visit Date|Date of Service|DOS)[:.\s]*([\d\/\-\.]+)",
                        r"(?:Encounter Date|Visit Date|Date of Service|DOS)[:.\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
                    ]
                },
                "type": {
                    "type": "string",
                    "patterns": [
                        r"(?:Encounter Type|Visit Type|Type)[:.\s]*(.*?)(?:\n|$)"
                    ]
                },
                "reason": {
                    "type": "string",
                    "patterns": [
                        r"(?:Reason for Visit|Chief Complaint|CC)[:.\s]*(.*?)(?:\n\n|$)"
                    ]
                }
            }
        },
        "vital_signs": {
            "type": "object",
            "properties": {
                "temperature": {
                    "type": "string",
                    "patterns": [
                        r"(?:Temperature|Temp)[:.\s]*(\d+\.?\d*\s*[CF]?)"
                    ]
                },
                "blood_pressure": {
                    "type": "string",
                    "patterns": [
                        r"(?:BP|Blood Pressure)[:.\s]*(\d+\/\d+\s*(?:mmHg)?)"
                    ]
                },
                "pulse": {
                    "type": "string",
                    "patterns": [
                        r"(?:Pulse|HR|Heart Rate)[:.\s]*(\d+\s*(?:bpm)?)"
                    ]
                },
                "respiratory_rate": {
                    "type": "string",
                    "patterns": [
                        r"(?:RR|Respiratory Rate|Respiration)[:.\s]*(\d+\s*(?:\/min)?)"
                    ]
                },
                "weight": {
                    "type": "string",
                    "patterns": [
                        r"(?:Weight|Wt)[:.\s]*(\d+\.?\d*\s*(?:kg|lbs)?)"
                    ]
                },
                "height": {
                    "type": "string",
                    "patterns": [
                        r"(?:Height|Ht)[:.\s]*(\d+\'?\s*\d*\"?|\d+\.?\d*\s*(?:cm|in)?)"
                    ]
                }
            }
        },
        "assessment": {
            "type": "string",
            "patterns": [
                r"(?:Assessment|Impression|Diagnosis)[:.\s]*(.*?)(?:\n\n|$)"
            ]
        },
        "plan": {
            "type": "string",
            "patterns": [
                r"(?:Plan|Treatment Plan|Recommendation)[:.\s]*(.*?)(?:\n\n|$)"
            ]
        },
        "medications": {
            "type": "array",
            "patterns": [
                r"(?:Medications|Prescriptions|Meds)[:.\s]*(.*?)(?:\n\n|$)"
            ]
        },
        "allergies": {
            "type": "array",
            "patterns": [
                r"(?:Allergies|Adverse Reactions)[:.\s]*(.*?)(?:\n\n|$)"
            ]
        },
        "notes": {
            "type": "string",
            "patterns": [
                r"(?:Notes|Additional Notes|Comments)[:.\s]*(.*?)(?:\n\n|$)"
            ]
        }
    }
}