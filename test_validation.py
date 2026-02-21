from app.schema.item import ItemCreate
from pydantic import ValidationError

try:
    item = ItemCreate(
        name="Test Item",
        item_code="ITM001",
        category_id=1,
        stock=10,
        photo_base64="",
        photo_content_type="image/jpeg"
    )
    print("Success:", item)
except ValidationError as e:
    print("Error:", e.errors())
