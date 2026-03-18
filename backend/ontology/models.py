from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- Base Ontology Models ---

class OntologyConcept(BaseModel):
    """
    Base class for all ontology concepts.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OntologyClass(OntologyConcept):
    """
    Represents a class in the ontology (e.g., Project, Team).
    """
    pass

class OntologyInstance(OntologyConcept):
    """
    Represents an instance of a class (e.g., a specific Project).
    """
    properties: Dict[str, Any] = Field(default_factory=dict)

class SemanticRelation(BaseModel):
    """
    Represents a relationship between two instances.
    """
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

# --- Domain Specific Models ---

class Project(OntologyInstance):
    budget: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "Active"

class Team(OntologyInstance):
    lead_id: Optional[str] = None

class Developer(OntologyInstance):
    role: str
    skills: List[str] = []
    experience_years: int = 0

class Requirement(OntologyInstance):
    priority: str = "Medium"
    status: str = "Open"
    deadline: Optional[datetime] = None

class Task(OntologyInstance):
    estimated_hours: float = 0.0
    priority: str = "Medium"
    status: str = "To Do"
    assignee_id: Optional[str] = None
    requirement_id: Optional[str] = None

# --- API Request/Response Models ---

class EntityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = {}

class RelationCreate(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = {}

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
