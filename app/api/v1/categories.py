from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import DBSession
from app.models import Category, Item
from app.schema import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
def list_categories(db: DBSession) -> list[Category]:
    return db.scalars(select(Category).order_by(Category.id)).all()


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: DBSession) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: DBSession) -> Category:
    existing = db.scalar(
        select(Category).where(func.lower(Category.name) == payload.name.lower())
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists",
        )

    category = Category(name=payload.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, db: DBSession) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    existing = db.scalar(
        select(Category).where(
            func.lower(Category.name) == payload.name.lower(),
            Category.id != category_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists",
        )

    category.name = payload.name
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DBSession) -> None:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    has_item = db.scalar(select(Item.id).where(Item.category_id == category_id).limit(1))
    if has_item is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be deleted because it is used by items",
        )

    db.delete(category)
    db.commit()
