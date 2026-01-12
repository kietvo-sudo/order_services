#!/usr/bin/env python3
"""
Script to insert sample products into the database via API
Usage: python insert_products.py
"""

import requests
import json
from typing import List, Dict

# API base URL - adjust if needed
BASE_URL = "http://localhost:8000"

# Sample products data (without id, API will auto-generate)
SAMPLE_PRODUCTS = [
    {
        "name": "iPhone 15 Pro Max 256GB",
        "description": "Apple iPhone 15 Pro Max với màn hình 6.7 inch, chip A17 Pro, camera 48MP",
        "price": 29990000,
        "currency": "VND",
        "stock": 50,
        "status": "ACTIVE"
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "description": "Samsung Galaxy S24 Ultra 5G 256GB, bút S Pen, camera 200MP",
        "price": 28990000,
        "currency": "VND",
        "stock": 30,
        "status": "ACTIVE"
    },
    {
        "name": "MacBook Pro 14 inch M3",
        "description": "Apple MacBook Pro 14 inch với chip M3, 16GB RAM, 512GB SSD",
        "price": 45990000,
        "currency": "VND",
        "stock": 20,
        "status": "ACTIVE"
    },
    {
        "name": "Áo thun nam cổ tròn",
        "description": "Áo thun nam chất liệu cotton 100%, size M-L-XL",
        "price": 299000,
        "currency": "VND",
        "stock": 200,
        "status": "ACTIVE"
    },
    {
        "name": "Quần jean nam slim fit",
        "description": "Quần jean nam kiểu dáng slim fit, màu xanh đen",
        "price": 890000,
        "currency": "VND",
        "stock": 150,
        "status": "ACTIVE"
    },
    {
        "name": "Giày thể thao Nike Air Max",
        "description": "Giày thể thao Nike Air Max 270, size 40-44",
        "price": 3490000,
        "currency": "VND",
        "stock": 80,
        "status": "ACTIVE"
    },
    {
        "name": "Túi xách da thật",
        "description": "Túi xách nữ da bò thật, thiết kế sang trọng",
        "price": 2490000,
        "currency": "VND",
        "stock": 45,
        "status": "ACTIVE"
    },
    {
        "name": "Tai nghe AirPods Pro 2",
        "description": "Apple AirPods Pro thế hệ 2, chống ồn chủ động, sạc không dây",
        "price": 7490000,
        "currency": "VND",
        "stock": 100,
        "status": "ACTIVE"
    },
    {
        "name": "Đồng hồ thông minh Apple Watch Series 9",
        "description": "Apple Watch Series 9 45mm, GPS, dây cao su",
        "price": 11990000,
        "currency": "VND",
        "stock": 60,
        "status": "ACTIVE"
    },
    {
        "name": "Loa Bluetooth JBL Flip 6",
        "description": "Loa Bluetooth JBL Flip 6, chống nước IPX7, pin 12 giờ",
        "price": 3490000,
        "currency": "VND",
        "stock": 120,
        "status": "ACTIVE"
    }
]


def insert_products(products: List[Dict], base_url: str = BASE_URL):
    """Insert products via API"""
    url = f"{base_url}/products"
    
    print(f"Inserting {len(products)} products to {url}...")
    print("-" * 60)
    
    success_count = 0
    failed_count = 0
    
    for i, product in enumerate(products, 1):
        try:
            response = requests.post(url, json=product)
            if response.status_code == 201:
                created = response.json()
                print(f"✓ [{i}/{len(products)}] Created: {created.get('name')} (ID: {created.get('id')})")
                success_count += 1
            else:
                print(f"✗ [{i}/{len(products)}] Failed: {product['name']}")
                print(f"  Status: {response.status_code}, Error: {response.text}")
                failed_count += 1
        except Exception as e:
            print(f"✗ [{i}/{len(products)}] Error: {product['name']}")
            print(f"  Exception: {str(e)}")
            failed_count += 1
    
    print("-" * 60)
    print(f"Summary: {success_count} succeeded, {failed_count} failed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    
    insert_products(SAMPLE_PRODUCTS, BASE_URL)

