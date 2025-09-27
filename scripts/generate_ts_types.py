import os
import sys
import pathlib
import subprocess

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
JSON_SCHEMA_DIR_NAME = "json-schemas"
TS_TYPES_DIR_NAME = "typescript-types"

JSON_SCHEMA_DIR = PROJECT_ROOT / JSON_SCHEMA_DIR_NAME
TS_TYPES_DIR = PROJECT_ROOT / TS_TYPES_DIR_NAME

JSTT_COMMAND = ["npx", "json-schema-to-typescript"]

def generate_ts_types():
    """Generates TypeScript types from JSON schema files."""
    if not JSON_SCHEMA_DIR.is_dir():
        print(f"Error: JSON schema directory '{JSON_SCHEMA_DIR}' not found.")
        print("Please run the 'generate_json_schemas.py' script first.")
        sys.exit(1)

    TS_TYPES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating TypeScript types in: {TS_TYPES_DIR}")

    generated_count = 0
    errors = []

    json_files = list(JSON_SCHEMA_DIR.glob("*.json"))
    if not json_files:
        print(f"No JSON schema files found in {JSON_SCHEMA_DIR}.")
        sys.exit(0)

    for json_file in json_files:
        model_name = json_file.stem
        output_filename = f"{model_name}.d.ts"
        output_path = TS_TYPES_DIR / output_filename

        command = JSTT_COMMAND + ["-i", str(json_file), "-o", str(output_path)]

        print(f"\nGenerating {output_filename} from {json_file.name}...")
        print(f"  Running command: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False, 
                shell=False 
            )

            if result.returncode == 0:
                print(f"  Successfully wrote type definition to {output_path.relative_to(PROJECT_ROOT)}")
                generated_count += 1
            else:
                error_msg = f"  Error generating type for {model_name}:\n    Exit Code: {result.returncode}\n    Stderr: {result.stderr.strip()}\n    Stdout: {result.stdout.strip()}"
                print(error_msg)
                errors.append(error_msg)
                if output_path.exists() and output_path.stat().st_size == 0:
                    output_path.unlink()


        except FileNotFoundError:
             error_msg = f"  Error: Command '{JSTT_COMMAND[0]}' not found. Make sure json-schema-to-typescript is installed and accessible (e.g., via npm/npx in your PATH)."
             print(error_msg)
             errors.append(error_msg)
             break
        except Exception as e:
            error_msg = f"  Unexpected error running command for {model_name}: {e}"
            print(error_msg)
            errors.append(error_msg)


    print(f"\nTypeScript type generation complete. Generated {generated_count} files.")
    if errors:
        print("\nErrors encountered:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)

if __name__ == "__main__":
    generate_ts_types()
