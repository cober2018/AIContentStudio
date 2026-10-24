from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, require_editor
from ..models import MaterialKind, SourceType, User
from ..services import knowledge_collections as collections
from ..services import library_usage, system_library

router = APIRouter(prefix="/api/v1", tags=["system-library"])
ResourceType = Literal["material", "source", "fact_pack", "knowledge_collection"]
PositiveID = Annotated[int, Field(strict=True, gt=0)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
DB = Annotated[Session, Depends(get_db)]
Reader = Annotated[User, Depends(get_current_user)]
Editor = Annotated[User, Depends(require_editor)]
Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LibraryFilters(Payload):
    type: ResourceType | None = None
    q: str | None = Field(default=None, max_length=300)
    status: Literal["active", "archived", "draft", "frozen"] | None = None
    material_kind: MaterialKind | None = None
    source_type: SourceType | None = None
    rights: Literal["allowed", "denied", "unknown", "revoked"] | None = None
    collection_id: int | None = Field(default=None, gt=0)
    material_source_kind: Literal["upload", "web_search", "ai_generated", "chart", "screenshot", "upstream", "legacy",
                                  "external_execution", "drive"] | None = None
    model_use: Literal["allowed", "denied", "unknown", "revoked"] | None = None
    material_source_id: int | None = Field(default=None, gt=0)
    material_collection_id: int | None = Field(default=None, gt=0)
    place: Literal["external", "common", "project"] | None = None
    place_project_id: int | None = Field(default=None, gt=0)
    order: Literal["oldest", "newest"] = "oldest"
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class CollectionCreate(Payload):
    name: Name
    description: str | None = Field(default=None, max_length=5000)


class RevisionPayload(Payload):
    expected_revision: PositiveID


class CollectionEdit(RevisionPayload):
    name: Name | None = None
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def fields_valid(self):
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        if not self.model_fields_set.intersection({"name", "description"}):
            raise ValueError("At least one edit required")
        return self


class ItemCreate(RevisionPayload):
    item_type: Literal["source_document", "fact_pack"]
    source_document_id: PositiveID | None = None
    fact_pack_id: PositiveID | None = None
    sort_order: int = Field(default=0, strict=True, ge=0, le=1000000)
    note: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def resource_valid(self):
        if (
            self.item_type == "source_document" and self.source_document_id is not None and self.fact_pack_id is None
        ) or (self.item_type == "fact_pack" and self.fact_pack_id is not None and self.source_document_id is None):
            return self
        raise ValueError("Exactly one matching resource ID required")


class ItemEdit(RevisionPayload):
    sort_order: int | None = Field(default=None, strict=True, ge=0, le=1000000)
    note: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def fields_valid(self):
        if "sort_order" in self.model_fields_set and self.sort_order is None:
            raise ValueError("sort_order cannot be null")
        if not self.model_fields_set.intersection({"sort_order", "note"}):
            raise ValueError("At least one edit required")
        return self


class Reorder(RevisionPayload):
    item_ids: list[PositiveID] = Field(max_length=10000)


@router.get("/system-library")
def list_library(db: DB, user: Reader, filters: Annotated[LibraryFilters, Query()]):
    values = filters.model_dump(mode="json")
    if values.get("material_collection_id"):
        from ..models import MaterialCollection

        collection = db.get(MaterialCollection, values["material_collection_id"])
        if collection is None or collection.owner_user_id != user.id:
            raise HTTPException(404, {"code": "material_collection_not_found"})
    place, place_project = values.pop("place", None), values.pop("place_project_id", None)
    from ..services import project_folders

    # 小样 / 成片 are a project's results, not material.
    values["exclude_material_ids"] = project_folders.output_material_ids(db)
    if place:
        # Where a file sits is read from the drive, so the matching ids are worked out before the query.
        # A project also shows what it reuses from other projects (shortcuts) and from 通用素材库.
        values["material_ids"] = [item["material_id"] for item in project_folders.tree(db)["items"]
                                  if (item["library"] == place and (not place_project or item["project_id"] == place_project))
                                  or (place == "project" and place_project and place_project in item["used_by"])]
    return system_library.list_library(db, values, values.pop("limit"), values.pop("offset"))


@router.get("/system-library/summary")
def library_summary(db: DB, user: Reader):
    return system_library.summary(db)


@router.get("/system-library/material/{material_id}/revisions")
def material_revisions(material_id: int, db: DB, user: Reader, limit: Limit = 50, offset: Offset = 0):
    return system_library.material_revisions(db, material_id, limit, offset)


@router.get("/system-library/material/{material_id}/revisions/{revision_id}")
def material_revision(material_id: int, revision_id: int, db: DB, user: Reader):
    return system_library.material_revision(db, material_id, revision_id)


@router.get("/system-library/{resource_type}/{resource_id}")
def resource_detail(resource_type: ResourceType, resource_id: int, db: DB, user: Reader):
    return system_library.resource_detail(db, resource_type, resource_id)


@router.get("/system-library/{resource_type}/{resource_id}/usage")
def resource_usage(
    resource_type: ResourceType, resource_id: int, db: DB, user: Reader, limit: Limit = 20, offset: Offset = 0
):
    return library_usage.usage(db, user, resource_type, resource_id, limit, offset)


@router.get("/knowledge-collections")
def list_collections(
    db: DB,
    user: Reader,
    status: Literal["active", "archived"] | None = None,
    q: Annotated[str | None, Query(max_length=300)] = None,
    limit: Limit = 50,
    offset: Offset = 0,
):
    return collections.list_collections(db, status, q, limit, offset)


@router.post("/knowledge-collections", status_code=201)
def create_collection(payload: CollectionCreate, db: DB, user: Editor):
    return collections.create_collection(db, user, payload.model_dump())


@router.get("/knowledge-collections/{collection_id}")
def get_collection(collection_id: int, db: DB, user: Reader):
    return collections.collection_dict(collections.get_collection(db, collection_id))


@router.patch("/knowledge-collections/{collection_id}")
def edit_collection(collection_id: int, payload: CollectionEdit, db: DB, user: Editor):
    return collections.edit_collection(db, collection_id, payload.model_dump(exclude_unset=True))


@router.delete("/knowledge-collections/{collection_id}")
def archive_collection(collection_id: int, expected_revision: Annotated[int, Query(gt=0)], db: DB, user: Editor):
    return collections.archive_collection(db, collection_id, expected_revision)


@router.get("/knowledge-collections/{collection_id}/items")
def list_items(
    collection_id: int,
    db: DB,
    user: Reader,
    status: Literal["active", "detached"] = "active",
    limit: Limit = 50,
    offset: Offset = 0,
):
    return collections.list_items(db, collection_id, status, limit, offset)


@router.post("/knowledge-collections/{collection_id}/items", status_code=201)
def add_item(collection_id: int, payload: ItemCreate, db: DB, user: Editor):
    return collections.add_item(db, user, collection_id, payload.model_dump())


@router.patch("/knowledge-collections/{collection_id}/items/{item_id}")
def edit_item(collection_id: int, item_id: int, payload: ItemEdit, db: DB, user: Editor):
    return collections.edit_item(db, collection_id, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/knowledge-collections/{collection_id}/items/{item_id}")
def detach_item(collection_id: int, item_id: int, expected_revision: Annotated[int, Query(gt=0)], db: DB, user: Editor):
    return collections.edit_item(db, collection_id, item_id, {"expected_revision": expected_revision}, detach=True)


@router.post("/knowledge-collections/{collection_id}/reorder")
def reorder(collection_id: int, payload: Reorder, db: DB, user: Editor):
    return collections.reorder(db, collection_id, payload.model_dump())
