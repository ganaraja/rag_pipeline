"""
Generic Pydantic models for AI application API.

These models provide the basic structure for collection management.
Extend with your custom models as needed.
"""

from pydantic import BaseModel, Field
from typing import Optional


# Collection Management Models (Reusable)

class CreateCollectionRequest(BaseModel):
    """Request model for creating a collection."""
    collection_name: str = Field(..., min_length=1, description="Name of the collection to create")


class CreateCollectionResponse(BaseModel):
    """Response model for collection creation."""
    success: bool
    collection_name: str
    message: str


class DeleteCollectionResponse(BaseModel):
    """Response model for collection deletion."""
    success: bool
    message: str


# TODO: Add your custom models below
# Example:
# class YourCustomRequest(BaseModel):
#     field1: str
#     field2: int
#
# class YourCustomResponse(BaseModel):
#     success: bool
#     data: dict
