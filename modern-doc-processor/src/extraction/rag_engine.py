# src/extraction/rag_engine.py
import asyncio
import json
import logging
import os
import re
from pathlib import Path
import openai
import random

logger = logging.getLogger(__name__)

class RAGEngine:
    """Extraction engine using Retrieval Augmented Generation with OpenAI"""
    
    def __init__(self, config):
        # Set up OpenAI API
        openai.api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        self.model = config.llm_model
        self.temperature = config.temperature
        
        # Load example documents if available
        self.examples = self._load_examples(config.examples_directory)
        
    def _load_examples(self, examples_dir):
        """Load example documents for each document class"""
        examples = {}
        
        try:
            examples_path = Path(examples_dir)
            if not examples_path.exists():
                logger.warning(f"Examples directory not found: {examples_dir}")
                return examples
                
            for class_dir in examples_path.iterdir():
                if class_dir.is_dir():
                    doc_class = class_dir.name
                    class_examples = []
                    
                    for example_file in class_dir.glob("*.json"):
                        try:
                            with open(example_file, "r", encoding="utf-8") as f:
                                example = json.load(f)
                                class_examples.append(example)
                        except Exception as e:
                            logger.error(f"Error loading example {example_file}: {str(e)}")
                            
                    if class_examples:
                        examples[doc_class] = class_examples
                        logger.info(f"Loaded {len(class_examples)} examples for class {doc_class}")
                        
            return examples
            
        except Exception as e:
            logger.error(f"Error loading examples: {str(e)}")
            return {}
            
    async def extract_data(self, text, doc_class, schema):
        """Extract structured data from document text using RAG"""
        try:
            # Get examples for this document class
            class_examples = self.examples.get(doc_class, [])
            
            # Select up to 2 random examples if available
            if class_examples:
                selected_examples = random.sample(
                    class_examples, min(2, len(class_examples))
                )
            else:
                selected_examples = []
                
            # Create prompt for extraction
            prompt = self._create_extraction_prompt(
                text, doc_class, schema, selected_examples
            )
            
            # Call OpenAI API
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert document data extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=2000
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", result_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON between curly braces
                json_match = re.search(r"({[\s\S]*})", result_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = result_text
                    
            # Parse the JSON
            try:
                extracted_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from LLM response: {result_text}")
                
                # Try to fix common JSON errors
                fixed_json = self._fix_json(json_str)
                try:
                    extracted_data = json.loads(fixed_json)
                except:
                    # Fall back to empty object with schema structure
                    extracted_data = self._create_empty_schema_result(schema)
                    
            # Validate against schema
            validated_data = self._validate_against_schema(extracted_data, schema)
            
            return validated_data
            
        except Exception as e:
            logger.error(f"RAG extraction error: {str(e)}")
            return self._create_empty_schema_result(schema)
            
    def _create_extraction_prompt(self, text, doc_class, schema, examples):
        """Create prompt for extraction"""
        # Convert schema to readable format
        schema_str = json.dumps(schema, indent=2)
        
        # Format examples
        examples_str = ""
        if examples:
            for i, example in enumerate(examples):
                examples_str += f"\nExample {i+1}:\n"
                examples_str += json.dumps(example, indent=2)
                examples_str += "\n"
        
        prompt = f"""
Please extract structured information from this {doc_class} document.

Here is the data schema to follow:
{schema_str}

{examples_str if examples else ""}

Here is the document text:
{text}

Extract all the relevant information and return it as a valid JSON object that matches the schema.
Only include fields you have high confidence in. If a field is not found, you can omit it.
For numeric values, return numbers without currency symbols or thousand separators.

Please format your response as valid JSON.
"""
        return prompt
        
    def _fix_json(self, json_str):
        """Attempt to fix common JSON formatting errors"""
        # Replace single quotes with double quotes
        fixed = json_str.replace("'", "\"")
        
        # Add quotes around unquoted keys
        fixed = re.sub(r'(\s*?)(\w+)(\s*?):', r'\1"\2"\3:', fixed)
        
        # Fix trailing commas
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        
        return fixed
        
    def _validate_against_schema(self, data, schema):
        """Validate extracted data against schema and fix issues"""
        result = {}
        
        # Process each field in the schema
        for field_name, field_info in schema.get("properties", {}).items():
            field_type = field_info.get("type", "string")
            
            # Check if field exists in data
            if field_name in data:
                value = data[field_name]
                
                # Type checking and conversion
                if field_type == "string" and not isinstance(value, str):
                    result[field_name] = str(value)
                elif field_type == "number" and not isinstance(value, (int, float)):
                    try:
                        if isinstance(value, str):
                            # Remove non-numeric characters except decimal point
                            numeric_value = re.sub(r"[^\d.]", "", value)
                            result[field_name] = float(numeric_value)
                        else:
                            result[field_name] = 0.0
                    except:
                        result[field_name] = 0.0
                elif field_type == "integer" and not isinstance(value, int):
                    try:
                        if isinstance(value, (str, float)):
                            result[field_name] = int(float(re.sub(r"[^\d.]", "", str(value))))
                        else:
                            result[field_name] = 0
                    except:
                        result[field_name] = 0
                elif field_type == "array" and not isinstance(value, list):
                    if isinstance(value, str):
                        result[field_name] = [item.strip() for item in value.split(",")]
                    else:
                        result[field_name] = []
                elif field_type == "object" and not isinstance(value, dict):
                    result[field_name] = {}
                else:
                    result[field_name] = value
            elif "default" in field_info:
                result[field_name] = field_info["default"]
                
        return result
        
    def _create_empty_schema_result(self, schema):
        """Create empty result structure based on schema"""
        result = {}
        
        # Add default values for each field
        for field_name, field_info in schema.get("properties", {}).items():
            field_type = field_info.get("type", "string")
            
            if "default" in field_info:
                result[field_name] = field_info["default"]
            else:
                if field_type == "string":
                    result[field_name] = ""
                elif field_type == "number":
                    result[field_name] = 0.0
                elif field_type == "integer":
                    result[field_name] = 0
                elif field_type == "array":
                    result[field_name] = []
                elif field_type == "object":
                    result[field_name] = {}
                else:
                    result[field_name] = None
                    
        return result