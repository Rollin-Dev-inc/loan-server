from datetime import date, timedelta

def test_create_loan(client, auth_headers, db):
    # First create category and item
    cat_res = client.post("/api/v1/categories/", json={"name": "Tools"}, headers=auth_headers)
    category_id = cat_res.json()["id"]

    photo_b64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2wBDAQUDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/yQALCAABAAEBAREA/8wABgAQEAX/2wBDAQUDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2P/g"
    item_res = client.post("/api/v1/items/", json={
        "name": "Screwdriver",
        "item_code": "SD001",
        "category_id": category_id,
        "stock": 5,
        "photo_base64": photo_b64,
        "photo_content_type": "image/jpeg"
    }, headers=auth_headers)
    item_id = item_res.json()["id"]

    loan_data = {
        "borrower_name": "John Doe",
        "item_id": item_id,
        "duration_days": 7,
        "borrowed_at": str(date.today()),
        "price_to_pay": 50000
    }

    response = client.post("/api/v1/loans/", json=loan_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["borrower_name"] == "John Doe"

def test_get_loans(client, auth_headers):
    response = client.get("/api/v1/loans/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
