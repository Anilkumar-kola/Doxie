# src/extraction/schemas/invoice.py

INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {
            "type": "string",
            "patterns": [
                r"(?:Invoice|Reference|Order)[\s#:]*([A-Z0-9\-]{3,20})",
                r"(?:INV|INVOICE)[\s#:]*([A-Z0-9\-]{3,20})"
            ]
        },
        "date": {
            "type": "string",
            "patterns": [
                r"(?:Date|Invoice Date)[:.\s]*([\d\/\-\.]+)",
                r"(?:Date|Invoice Date)[:.\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
            ]
        },
        "due_date": {
            "type": "string",
            "patterns": [
                r"(?:Due Date|Payment Due)[:.\s]*([\d\/\-\.]+)",
                r"(?:Due Date|Payment Due)[:.\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
            ]
        },
        "vendor": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "patterns": [
                        r"(?:^|\n)([A-Z][A-Za-z0-9\s,\.]+)(?:\n|$)",
                        r"(?:From|Vendor|Supplier|Billed From|Company)[:.\s]*(.*?)(?:\n|$)"
                    ]
                },
                "address": {
                    "type": "string",
                    "patterns": [
                        r"(?:Address|Location)[:.\s]*(.*?)(?:\n\n|$)",
                        r"(?:\n)([A-Za-z0-9\s\.,#\-]+(?:\n[A-Za-z0-9\s\.,#\-]+){1,4})(?:\n\n|$)"
                    ]
                },
                "phone": {
                    "type": "string",
                    "patterns": [
                        r"(?:Phone|Tel|Contact|Ph)[:.\s]*([\+\(\)\d\s\-\.]{10,})"
                    ]
                },
                "email": {
                    "type": "string",
                    "patterns": [
                        r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"
                    ]
                },
                "tax_id": {
                    "type": "string",
                    "patterns": [
                        r"(?:Tax ID|VAT|GST|EIN|ABN)[:.\s#]*([\w\-]+)"
                    ]
                }
            }
        },
        "customer": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "patterns": [
                        r"(?:Bill To|Customer|Client|Recipient|To)[:.\s]*(.*?)(?:\n|$)"
                    ]
                },
                "address": {
                    "type": "string",
                    "patterns": [
                        r"(?:Bill To Address|Shipping Address|Deliver To)[:.\s]*(.*?)(?:\n\n|$)"
                    ]
                },
                "id": {
                    "type": "string",
                    "patterns": [
                        r"(?:Customer ID|Account|Customer No|Client ID)[:.\s#]*([\w\-]+)"
                    ]
                }
            }
        },
        "subtotal": {
            "type": "number",
            "patterns": [
                r"(?:Subtotal|Sub-total|Net)[:.\s]*[$€£]*\s*([\d,]+\.?\d*)",
                r"(?:Subtotal|Sub-total|Net)[^$€£\n\d]*[$€£]*\s*([\d,]+\.?\d*)"
            ]
        },
        "tax": {
            "type": "number",
            "patterns": [
                r"(?:Tax|VAT|GST|HST)[:.\s]*[$€£]*\s*([\d,]+\.?\d*)",
                r"(?:Tax|VAT|GST|HST)[^$€£\n\d]*[$€£]*\s*([\d,]+\.?\d*)"
            ]
        },
        "total": {
            "type": "number",
            "patterns": [
                r"(?:Total|Amount Due|Balance Due|TOTAL)[:.\s]*[$€£]*\s*([\d,]+\.?\d*)",
                r"(?:Total|Amount Due|Balance Due|TOTAL)[^$€£\n\d]*[$€£]*\s*([\d,]+\.?\d*)"
            ]
        },
        "currency": {
            "type": "string",
            "patterns": [
                r"(?:Currency|Denomination)[:.\s]*([$€£A-Z]{1,3})",
                r"(?:Amount|Total|Balance)[^$€£\n\d]*([$€£A-Z]{1,3})"
            ]
        },
        "payment_terms": {
            "type": "string",
            "patterns": [
                r"(?:Terms|Payment Terms|Due)[:.\s]*(.*?)(?:\n|$)"
            ]
        },
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string"
                    },
                    "quantity": {
                        "type": "number"
                    },
                    "unit_price": {
                        "type": "number"
                    },
                    "total": {
                        "type": "number"
                    }
                }
            }
        },
        "notes": {
            "type": "string",
            "patterns": [
                r"(?:Notes|Comments|Additional Information)[:.\s]*(.*?)(?:\n\n|$)"
            ]
        }
    }
}

RECEIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "merchant": {
            "type": "string",
            "patterns": [
                r"(?:^|\n)([A-Z][A-Za-z0-9\s,\.]+)(?:\n|$)",
                r"(?:Store|Merchant|Vendor|Retailer)[:.\s]*(.*?)(?:\n|$)"
            ]
        },
        "date": {
            "type": "string",
            "patterns": [
                r"(?:Date|Receipt Date)[:.\s]*([\d\/\-\.]+)",
                r"(?:Date|Receipt Date)[:.\s]*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
            ]
        },
        "time": {
            "type": "string",
            "patterns": [
                r"(?:Time)[:.\s]*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)"
            ]
        },
        "receipt_number": {
            "type": "string",
            "patterns": [
                r"(?:Receipt|Transaction|Ref|Reference)[\s#:]*([A-Z0-9\-]{3,20})"
            ]
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string"
                    },
                    "quantity": {
                        "type": "number"
                    },
                    "unit_price": {
                        "type": "number"
                    },
                    "total": {
                        "type": "number"
                    }
                }
            }
        },
        "subtotal": {
            "type": "number",
            "patterns": [
                r"(?:Subtotal|Sub-total|Net)[:.\s]*[$€£]*\s*([\d,]+\.?\d*)"
            ]
        },
        "tax": {
            "type": "number",
            "patterns": [
                r"(?:Tax|VAT|GST|HST|Sales Tax)[:.\s]*[$€£]*\s*([\d,]+\.?\d*)"
            ]
        },
        "total": {
            "type": "number",
            "patterns": [
                r"(?:Total|Amount|TOTAL)[:.\s]*[$€£]*\s*([\d,]+\.?\d*)"
            ]
        },
        "payment_method": {
            "type": "string",
            "patterns": [
                r"(?:Payment|Paid By|Method|Payment Method|Tender)[:.\s]*(.*?)(?:\n|$)"
            ]
        },
        "cashier": {
            "type": "string",
            "patterns": [
                r"(?:Cashier|Server|Associate|Clerk|Operator)[:.\s]*(.*?)(?:\n|$)"
            ]
        },
        "store_id": {
            "type": "string",
            "patterns": [
                r"(?:Store ID|Location|Branch)[:.\s#]*([\w\-]+)"
            ]
        }
    }
}