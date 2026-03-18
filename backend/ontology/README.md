# Ontology Module

This module implements an Ontology Knowledge Graph system using Neo4j.

## Setup

1.  **Install Neo4j**: Ensure you have a Neo4j database running (local or AuraDB).
2.  **Environment Variables**: Add the following to your `.env` file in the `backend` directory (or root):

    ```env
    NEO4J_URI=bolt://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_password
    ```

3.  **Dependencies**: The required Python package `neo4j` is added to `requirements.txt`.

## Data Model

The system manages 5 core entities:
- **Project**: Represents a software project.
- **Team**: Represents a team working on a project.
- **Developer**: Represents a developer in a team.
- **Requirement**: Represents a functional or non-functional requirement.
- **Task**: Represents a unit of work.

## Relationships

- `Project` -[HAS_TEAM]-> `Team`
- `Team` -[HAS_DEVELOPER]-> `Developer`
- `Project` -[HAS_REQUIREMENT]-> `Requirement`
- `Task` -[OF]-> `Requirement`
- `Task` -[ASSIGNED_TO]-> `Developer`

## API Endpoints

- `POST /api/v1/ontology/projects`: Create a project
- `POST /api/v1/ontology/teams`: Create a team
- `POST /api/v1/ontology/developers`: Create a developer
- `POST /api/v1/ontology/requirements`: Create a requirement
- `POST /api/v1/ontology/tasks`: Create a task
- `POST /api/v1/ontology/relations`: Create a relationship
- `GET /api/v1/ontology/search?q=...`: Semantic search

## Semantic Search

The search endpoint uses Neo4j Fulltext Indexes to find relevant nodes and returns them along with their immediate context (connected nodes).
