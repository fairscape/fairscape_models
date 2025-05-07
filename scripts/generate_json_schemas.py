import os
import sys
import pathlib
import importlib
import inspect
import json
from pydantic import BaseModel

#this script is in root/scripts/ and models are in root/fairscape_models/
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
SOURCE_DIR_NAME = "fairscape_models"
OUTPUT_DIR_NAME = "json-schemas"

SOURCE_DIR = PROJECT_ROOT / SOURCE_DIR_NAME
OUTPUT_DIR = PROJECT_ROOT / OUTPUT_DIR_NAME

sys.path.insert(0, str(PROJECT_ROOT))

def find_pydantic_models(module):
    """Finds Pydantic models defined directly within a module."""
    models = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseModel) and obj is not BaseModel:
            if obj.__module__ == module.__name__:
                models.append((name, obj))
    return models

def generate_schemas():
    """Generates JSON schemas for all Pydantic models found."""
    if not SOURCE_DIR.is_dir():
        print(f"Error: Source directory '{SOURCE_DIR}' not found.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating JSON schemas in: {OUTPUT_DIR}")

    generated_count = 0
    errors = []

    for py_file in SOURCE_DIR.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        module_name = f"{SOURCE_DIR_NAME}.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)
            models_in_module = find_pydantic_models(module)

            if not models_in_module:
                continue

            print(f"\nProcessing {py_file.name}...")
            for model_name, model_cls in models_in_module:
                try:
                    print(f"  Generating schema for: {model_name}")
                    schema = model_cls.model_json_schema()
                    output_filename = f"{model_name}.json"
                    output_path = OUTPUT_DIR / output_filename

                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(schema, f, indent=2)
                    generated_count += 1
                    print(f"    Successfully wrote schema to {output_path.relative_to(PROJECT_ROOT)}")

                except Exception as e:
                    error_msg = f"    Error generating schema for {model_name}: {e}"
                    print(error_msg)
                    errors.append(error_msg)

        except ImportError as e:
            error_msg = f"Error importing module {module_name}: {e}"
            print(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error processing {py_file.name}: {e}"
            print(error_msg)
            errors.append(error_msg)


    print(f"\nSchema generation complete. Generated {generated_count} schemas.")
    if errors:
        print("\nErrors encountered:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)

if __name__ == "__main__":
    generate_schemas()