import re
import uuid
from typing import List, Dict, Any, Optional

def ro_crate_id_to_croissant_local_id(ro_crate_id: str, prefix: str = "") -> str:
    if not ro_crate_id:
        return f"#{prefix}{uuid.uuid4().hex[:8]}"
    safe_id_part = ro_crate_id.split('/')[-1].replace('.', '-').replace(':', '-')
    return f"#{prefix}{safe_id_part}"

def map_schema_type_to_croissant_data_type(schema_type: str) -> str:
    type_map = {
        "string": "sc:Text",
        "integer": "sc:Integer",
        "number": "sc:Float",
        "boolean": "sc:Boolean",
        "array": "rdf:List",
        "object": "sc:Thing",
        "null": "sc:Text",
    }
    return type_map.get(schema_type.lower(), "sc:Text")

def parse_authors_to_person_list(authors_data: Any) -> Optional[List[Dict[str, Any]]]:
    if not authors_data: 
        return None
    
    names_to_process = []
    if isinstance(authors_data, str):
        names_to_process = [name.strip() for name in authors_data.replace(';', ',').split(',') if name.strip()]
    elif isinstance(authors_data, list):
        names_to_process = [str(name).strip() for name in authors_data if str(name).strip()]
    
    if not names_to_process: 
        return []
    
    return [{"@type": "sc:Person", "name": name} for name in names_to_process]

def parse_cite_as(cite_data: Any) -> Optional[str]:
    if not cite_data:
        return None
    if isinstance(cite_data, list):
        return cite_data[0] if cite_data else None
    return str(cite_data)

def parse_publisher(publisher_data: Any) -> Optional[Dict[str, Any]]:
    if not publisher_data:
        return None
    if isinstance(publisher_data, str):
        return {"@type": "sc:Organization", "name": publisher_data}
    elif isinstance(publisher_data, dict):
        return publisher_data
    return {"@type": "sc:Organization", "name": str(publisher_data)}

def format_name(name_str: Optional[str]) -> Optional[str]:
    if not name_str:
        return None
    return name_str.replace(' ', '_')

def format_md5(md5_str: Optional[str]) -> str:
    if not md5_str:
        return "PLACEHOLDERMD5"
    return md5_str