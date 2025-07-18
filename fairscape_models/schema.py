from typing import (
        Optional,
        Dict,
        List,
        Union
)
from pydantic import (
    BaseModel,
    Field,
    field_validator
    )
import re
from enum import Enum 
from fairscape_models.fairscape_base import *

# TODO switch to ENUM for better clarification
class ItemTypeEnum(Enum):
    integer='integer'
    number='number'
    string='string'
    array='array'
    boolean='boolean'
    object='object'

class Property(BaseModel):
    description: str = Field(...)
    index: Union[str, int] = Field(...)
    type: str = Field(...)
    value_url: Optional[str] = Field(default = None, alias = 'value-url')
    pattern: Optional[str] = Field(default = None)
    min_items: Optional[int] = Field(default = None, alias = 'min-items')
    max_items: Optional[int] = Field(default = None, alias = 'max-items')
    unique_items: Optional[bool] = Field(default = None, alias = 'unique-items')
    properties: Optional[Dict[str, 'Property']] = Field(default=None)

    model_config = ConfigDict(extra='allow')

    @field_validator('index', mode='before')
    def validate_index(cls, value):
        if isinstance(value, str):
            # Allow something like int::int for index. Raise error if else
            pattern = r'^\d+$|^-?\d+::|^-?\d+::-?\d+$|^::-?\d+'
            if not re.match(pattern, value):
                raise ValueError("Index must match the pattern 'int::int'")
        return value

    @field_validator('pattern', mode='before')
    def validate_pattern(cls, value):
        if value is not None:
            try:
                re.compile(value)
            except re.error:
                raise ValueError("Pattern must be a valid regular expression")
        return value
    
    @field_validator('type', mode='before')
    def validate_property_type(cls, value):
        valid_types = {'integer', 'number', 'string', 'array','boolean', 'object'}
        if value is not None:
            if value not in valid_types:
                raise ValueError(f"Type must be one of {valid_types}")
        return value

class Schema(FairscapeEVIBaseModel):
    context: Dict[str, str] = Field( 
        default= {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"},
        alias="@context" 
    )
    metadataType: str = Field(alias="@type", default= "evi:Schema")
    properties: Dict[str, Property]
    schemaType: Optional[str] = Field(default="object", alias="type")
    additionalProperties: Optional[bool] = Field(default=True)
    required: Optional[List[str]] = []  
    separator: Optional[str] = Field(default=",")
    header: Optional[bool] = Field(default=True)
    examples: Optional[List[Dict]] = []
    model_config = ConfigDict(extra='allow')