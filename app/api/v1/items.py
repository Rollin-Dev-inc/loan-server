import base64

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.api.deps import DBSession
from app.models import Category, Item, Loan
from app.schema import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


def _decode_photo(photo_base64: str) -> bytes:
    base64_data = photo_base64.split("base64,", maxsplit=1)[-1]
    return base64.b64decode(base64_data)


@router.get("/", response_model=list[ItemRead])
def list_items(db: DBSession) -> list[Item]:
    return db.scalars(select(Item).order_by(Item.id)).all()


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, db: DBSession) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: DBSession) -> Item:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )

    existing_code = db.scalar(
        select(Item).where(Item.item_code == payload.item_code)
    )
    if existing_code is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item code already exists",
        )

    item = Item(
        name=payload.name,
        item_code=payload.item_code,
        category_id=payload.category_id,
        stock=payload.stock,
        photo_data=_decode_photo(payload.photo_base64),
        photo_content_type=payload.photo_content_type,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=ItemRead)
def update_item(item_id: int, payload: ItemUpdate, db: DBSession) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
        item.category_id = payload.category_id

    if payload.name is not None:
        item.name = payload.name

    if payload.item_code is not None:
        existing_code = db.scalar(
            select(Item).where(Item.item_code == payload.item_code, Item.id != item_id)
        )
        if existing_code is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Item code already exists",
            )
        item.item_code = payload.item_code

    if payload.stock is not None:
        item.stock = payload.stock

    if payload.photo_base64 is not None:
        item.photo_data = _decode_photo(payload.photo_base64)
        item.photo_content_type = payload.photo_content_type or item.photo_content_type
    elif payload.photo_content_type is not None:
        item.photo_content_type = payload.photo_content_type

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: DBSession) -> None:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    has_loan = db.scalar(select(Loan.id).where(Loan.item_id == item_id).limit(1))
    if has_loan is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item cannot be deleted because it is used by loan data",
        )

    db.delete(item)
    db.commit()


@router.get("/{item_id}/photo")
def get_item_photo(item_id: int, db: DBSession) -> Response:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    if not item.photo_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item photo not found",
        )
    return Response(content=item.photo_data, media_type=item.photo_content_type)
