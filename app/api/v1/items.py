import base64

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.api.deps import CurrentAdmin, CurrentUser, DBSession
from app.models import Category, Item, ItemPhoto, Loan
from app.schema import ItemCreate, ItemRead, ItemUpdate
from app.services.audit_service import record_audit
from app.services.cloudinary_service import destroy_image, upload_base64_image
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/items", tags=["items"])


def _decode_photo(photo_base64: str | None) -> bytes | None:
    if not photo_base64:
        return None
    base64_data = photo_base64.split("base64,", maxsplit=1)[-1]
    return base64.b64decode(base64_data)


@router.get("/", response_model=list[ItemRead])
def list_items(
    db: DBSession, 
    current_user: CurrentUser,
    q: str | None = None,
    category_id: int | None = None,
    in_stock: bool | None = None,
) -> list[Item]:
    query = select(Item)
    if q:
        query = query.where(Item.name.ilike(f"%{q}%") | Item.item_code.ilike(f"%{q}%"))
    if category_id is not None:
        query = query.where(Item.category_id == category_id)
    if in_stock is not None:
        if in_stock:
            query = query.where(Item.stock > 0)
        else:
            query = query.where(Item.stock == 0)
            
    return db.scalars(query.order_by(Item.id)).all()


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, db: DBSession, current_user: CurrentUser) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: DBSession, admin: CurrentAdmin) -> Item:
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

    photos = payload.photos_base64 or []
    
    photo_url = None
    photo_data = None
    photo_content_type = "image/jpeg"
    
    if len(photos) > 0:
        main_photo = photos[0]
        photo_url = upload_base64_image(main_photo, public_id=payload.item_code)
        if not photo_url:
            photo_data = _decode_photo(main_photo)

    item = Item(
        name=payload.name,
        item_code=payload.item_code,
        category_id=payload.category_id,
        stock=payload.stock,
        photo_data=photo_data,
        photo_url=photo_url,
        photo_content_type=photo_content_type if photo_data else None,
    )
    db.add(item)
    db.flush()

    for idx, photo in enumerate(photos[1:], start=1):
        sub_id = f"{payload.item_code}_{idx}"
        p_url = upload_base64_image(photo, public_id=sub_id)
        p_data = _decode_photo(photo) if not p_url else None
        db.add(ItemPhoto(
            item_id=item.id,
            photo_url=p_url,
            photo_data=p_data,
            photo_content_type=photo_content_type if p_data else None
        ))

    record_audit(db, admin.id, admin.username, "CREATE", "ITEM", item.id, item.item_code)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=ItemRead)
def update_item(item_id: int, payload: ItemUpdate, db: DBSession, admin: CurrentAdmin) -> Item:
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

    if payload.photos_base64 is not None:
        if item.photo_url:
            destroy_image(item.item_code)
        for prev_p in item.additional_photos:
            if prev_p.photo_url:
                # We can't know the exact index public_id, let's derive it or just delete prefix.
                destroy_image(prev_p.photo_url.split('/')[-1].split('.')[0].strip())
            db.delete(prev_p)
            
        photos = payload.photos_base64
        photo_url = None
        photo_data = None
        photo_content_type = "image/jpeg"
        
        if len(photos) > 0:
            main_photo = photos[0]
            photo_url = upload_base64_image(main_photo, public_id=item.item_code)
            if not photo_url:
                photo_data = _decode_photo(main_photo)
                
        item.photo_url = photo_url
        item.photo_data = photo_data
        item.photo_content_type = photo_content_type if photo_data else None

        for idx, photo in enumerate(photos[1:], start=1):
            sub_id = f"{item.item_code}_{idx}"
            p_url = upload_base64_image(photo, public_id=sub_id)
            p_data = _decode_photo(photo) if not p_url else None
            db.add(ItemPhoto(
                item_id=item.id,
                photo_url=p_url,
                photo_data=p_data,
                photo_content_type=photo_content_type if p_data else None
            ))

    record_audit(db, admin.id, admin.username, "UPDATE", "ITEM", item.id, item.item_code)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: DBSession, admin: CurrentAdmin) -> None:
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

    if item.photo_url:
        destroy_image(item.item_code)
    for prev_p in item.additional_photos:
        if prev_p.photo_url:
            destroy_image(prev_p.photo_url.split('/')[-1].split('.')[0].strip())


    record_audit(db, admin.id, admin.username, "DELETE", "ITEM", item.id, item.item_code)
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
    if item.photo_url:
        return RedirectResponse(url=item.photo_url)

    if not item.photo_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item photo not found",
        )
    return Response(content=item.photo_data, media_type=item.photo_content_type)


@router.get("/{item_id}/photos/{photo_id}")
def get_item_photo_additional(item_id: int, photo_id: int, db: DBSession) -> Response:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
        
    photo = db.get(ItemPhoto, photo_id)
    if photo is None or photo.item_id != item_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
        
    if photo.photo_url:
        return RedirectResponse(url=photo.photo_url)

    if not photo.photo_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item photo data not found",
        )
    return Response(content=photo.photo_data, media_type=photo.photo_content_type)
