from typing import Dict, Any, Optional, Type, List, Callable
from pydantic import BaseModel
from fairscape_models.rocrate import ROCrateV1_2

class ROCToTargetConverter:
    def __init__(self, source_crate: ROCrateV1_2, mapping_configuration: Dict[str, Any]):
        self.source_crate = source_crate
        self.mapping_config = mapping_configuration
        self.root_entity = self._find_root_entity()
        
        self.target_args_cache: Dict[str, Dict[str, Any]] = {}
        self.target_objects_cache: Dict[str, BaseModel] = {}
        self.final_object: Optional[BaseModel] = None

        if not self.root_entity:
            raise ValueError("Could not find the root dataset entity in the RO-Crate.")

    def _find_root_entity(self) -> Optional[BaseModel]:
        metadata_descriptor = next((e for e in self.source_crate.metadataGraph if e.guid == "ro-crate-metadata.json"), None)
        if metadata_descriptor and hasattr(metadata_descriptor, "about") and metadata_descriptor.about:
            root_id = metadata_descriptor.about.guid
            return next((e for e in self.source_crate.metadataGraph if e.guid == root_id), None)
        return None

    def convert(self) -> Optional[BaseModel]:
        self._create_argument_dictionaries()
        self._instantiate_models()
        self._build_and_assemble_final_object()
        return self.final_object

    def _get_context_hint(self, entity_guid: str) -> str:
        if self.root_entity and entity_guid == self.root_entity.guid:
            return "ROOT"
        return "COMPONENT"

    def _create_argument_dictionaries(self):
        for source_entity in self.source_crate.metadataGraph:
            if source_entity.guid == "ro-crate-metadata.json": continue
            
            entity_type_name = type(source_entity).__name__
            context_hint = self._get_context_hint(source_entity.guid)
            rule = self.mapping_config.get("entity_map", {}).get((entity_type_name, context_hint))
            
            if rule:
                target_args = self._map_source_to_args(
                    source_entity.model_dump(by_alias=True),
                    rule["mapping_def"]
                )
                self.target_args_cache[source_entity.guid] = target_args

    def _map_source_to_args(self, source_dict: Dict[str, Any], mapping_def: Dict[str, Any]) -> Dict[str, Any]:
        target_args = {}
        for target_key, spec in mapping_def.items():
            #fancy build handled later
            if "builder_func" in spec: continue
            value = None
            if "fixed_value" in spec:
                value = spec["fixed_value"]
            elif "source_key" in spec:
                value = source_dict.get(spec["source_key"])
                if "parser" in spec and value is not None:
                    value = spec["parser"](value)
            if value is not None:
                target_args[target_key] = value
        return target_args

    def _instantiate_models(self):
        for source_guid, args in self.target_args_cache.items():
            entity_type_name = type(next(e for e in self.source_crate.metadataGraph if e.guid == source_guid)).__name__
            context_hint = self._get_context_hint(source_guid)
            rule = self.mapping_config.get("entity_map", {}).get((entity_type_name, context_hint))
            if rule:
                try:
                    self.target_objects_cache[source_guid] = rule["target_class"](**args)
                except Exception as e:
                    print(f"Error instantiating {rule['target_class'].__name__} for source GUID {source_guid}")
                    print(f"With arguments: {args}")
                    raise e
    
    def _build_and_assemble_final_object(self):
        if not self.root_entity: return
        
        parent_object = self.target_objects_cache.get(self.root_entity.guid)
        if not parent_object: return

        root_rule = self.mapping_config.get("entity_map", {}).get((type(self.root_entity).__name__, "ROOT"))
        if root_rule:
            mapping_def = root_rule["mapping_def"]
            for target_key, spec in mapping_def.items():
                if "builder_func" in spec and spec["builder_func"]:
                    builder_func: Callable = spec["builder_func"]
                    value = builder_func(converter_instance=self, source_entity_model=self.root_entity)
                    if value is not None:
                        python_attr_name = self._get_python_attribute_name(parent_object, target_key)
                        setattr(parent_object, python_attr_name, value)
        
        for instruction in self.mapping_config.get("assembly_instructions", []):
            if not isinstance(parent_object, instruction["parent_type"]): continue
            
            parent_attr = instruction["parent_attribute"]
            child_type = instruction["child_type"]
            parent_list = []
            
            for child_object in self.target_objects_cache.values():
                if isinstance(child_object, child_type):
                    item_to_link = child_object
                    if "child_attribute_to_link" in instruction:
                        item_to_link = getattr(child_object, instruction["child_attribute_to_link"])
                    parent_list.append(item_to_link)
            
            python_attr_name = self._get_python_attribute_name(parent_object, parent_attr)
            setattr(parent_object, python_attr_name, parent_list)
        
        self.final_object = parent_object

    def _get_python_attribute_name(self, model_instance: BaseModel, field_key: str) -> str:
        for field_name, field_info in model_instance.model_fields.items():
            if field_info.alias == field_key or field_name == field_key:
                return field_name
        return field_key

    def _map_single_object_from_dict(self, source_dict: Dict[str, Any], mapping_def: Dict[str, Any]) -> Dict[str, Any]:
        return self._map_source_to_args(source_dict, mapping_def)