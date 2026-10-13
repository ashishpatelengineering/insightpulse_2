"""Generate five realistic sample datasets for InsightPulse.

Each dataset has a different column naming style and date format, but every one
contains everything needed by all four modes (CLV, Product Recommendation,
Market Basket Analysis and Forecasting):

    customer, invoice, date, product id, product name, category, sub category,
    quantity, unit price, sales, plus one extra business dimension.

Run:  python tools/generate_samples.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent.parent / "backend" / "data" / "samples"
START = pd.Timestamp("2023-10-01")
END = pd.Timestamp("2026-09-30")
N_MONTHS = 36


@dataclass
class Config:
    key: str
    filename: str
    seed: int
    n_customers: int
    invoices_by_tier: dict  # tier -> (min, max)
    tier_probs: tuple  # low, mid, high
    products: list  # (name, category, sub_category, price, popularity)
    bundles: list  # (name_a, name_b)
    bundle_prob: float
    extra_mean: float
    qty_lambda: dict  # category -> poisson lambda added to 1
    seasonality: list  # 12 values, Jan..Dec
    monthly_growth: float
    extra_dim_values: list
    id_prefix: str
    columns: dict
    date_format: str
    customer_fmt: str
    invoice_fmt: str
    customer_start: int
    invoice_start: int
    weekend_boost: float = 1.0
    sep: str = ","
    decimal: str = "."
    return_rate: float = 0.0  # share of lines that come back later as a negative row


DS_OFFICE = Config(
    key="office_home_retail",
    filename="sample_office_home_retail.csv",
    seed=11,
    n_customers=720,
    invoices_by_tier={"low": (1, 4), "mid": (5, 10), "high": (12, 26)},
    tier_probs=(0.42, 0.38, 0.20),
    products=[
        ("Ergonomic Office Chair", "Furniture", "Chairs", 189.99, 3),
        ("Mesh Task Chair", "Furniture", "Chairs", 109.00, 4),
        ("Executive Leather Chair", "Furniture", "Chairs", 299.00, 1.5),
        ("Standing Desk", "Furniture", "Desks", 349.00, 2),
        ("Compact Writing Desk", "Furniture", "Desks", 129.00, 3),
        ("L-Shaped Desk", "Furniture", "Desks", 259.00, 1.5),
        ("3-Drawer File Cabinet", "Furniture", "Storage", 99.00, 3),
        ("Bookshelf 5-Tier", "Furniture", "Storage", 89.00, 3),
        ("Storage Ottoman", "Furniture", "Storage", 59.00, 2),
        ("A4 Copy Paper 500 Sheets", "Office Supplies", "Paper", 6.49, 8),
        ("Sticky Notes Pack", "Office Supplies", "Paper", 4.29, 7),
        ("Spiral Notebook 3-Pack", "Office Supplies", "Paper", 8.99, 6),
        ("Ballpoint Pens 12-Pack", "Office Supplies", "Writing", 5.49, 8),
        ("Gel Pens Assorted", "Office Supplies", "Writing", 7.99, 5),
        ("Permanent Markers", "Office Supplies", "Writing", 6.99, 5),
        ("Highlighters 6-Pack", "Office Supplies", "Writing", 4.99, 5),
        ("Binder Clips Assorted", "Office Supplies", "Organizers", 3.49, 5),
        ("Desk Organizer", "Office Supplies", "Organizers", 19.99, 4),
        ("Document Folders 25-Pack", "Office Supplies", "Organizers", 9.99, 5),
        ("Wireless Mouse", "Technology", "Accessories", 24.99, 7),
        ("Mechanical Keyboard", "Technology", "Accessories", 79.99, 4),
        ("USB-C Hub", "Technology", "Accessories", 39.99, 4),
        ("Laptop Stand", "Technology", "Accessories", 34.99, 4),
        ("HD Webcam", "Technology", "Accessories", 59.99, 3),
        ("Laser Printer", "Technology", "Printing", 169.00, 1.5),
        ("Ink Cartridge Black", "Technology", "Printing", 29.99, 5),
        ("Ink Cartridge Color", "Technology", "Printing", 34.99, 4),
        ("Toner Cartridge", "Technology", "Printing", 54.99, 3),
        ("Noise Cancelling Headset", "Technology", "Audio", 89.00, 3),
        ("Desktop Speakers", "Technology", "Audio", 44.99, 2),
        ("LED Desk Lamp", "Home Decor", "Lighting", 29.99, 5),
        ("Floor Lamp", "Home Decor", "Lighting", 59.00, 2),
        ("Smart Bulb 4-Pack", "Home Decor", "Lighting", 24.99, 3),
        ("Framed Wall Art", "Home Decor", "Wall and Floor", 39.00, 3),
        ("Area Rug 5x7", "Home Decor", "Wall and Floor", 119.00, 1.5),
        ("Wall Clock", "Home Decor", "Wall and Floor", 22.99, 3),
    ],
    bundles=[
        ("Ergonomic Office Chair", "Standing Desk"),
        ("Wireless Mouse", "Mechanical Keyboard"),
        ("Laptop Stand", "USB-C Hub"),
        ("Laser Printer", "Toner Cartridge"),
        ("Ink Cartridge Black", "Ink Cartridge Color"),
        ("A4 Copy Paper 500 Sheets", "Ballpoint Pens 12-Pack"),
        ("Sticky Notes Pack", "Highlighters 6-Pack"),
        ("Desk Organizer", "Document Folders 25-Pack"),
        ("LED Desk Lamp", "Compact Writing Desk"),
        ("HD Webcam", "Noise Cancelling Headset"),
    ],
    bundle_prob=0.55,
    extra_mean=0.9,
    qty_lambda={"Furniture": 0.08, "Office Supplies": 1.1, "Technology": 0.15, "Home Decor": 0.2},
    seasonality=[0.95, 0.90, 0.95, 0.95, 0.95, 0.90, 0.95, 1.10, 1.15, 1.00, 1.35, 1.50],
    monthly_growth=0.006,
    extra_dim_values=["North", "South", "East", "West"],
    id_prefix="OH",
    columns={
        "customer": "CustomerID",
        "invoice": "InvoiceNo",
        "date": "InvoiceDate",
        "pid": "ProductID",
        "pname": "ProductName",
        "cat": "Category",
        "sub": "SubCategory",
        "qty": "Quantity",
        "price": "UnitPrice",
        "sales": "Sales",
        "extra": "Region",
    },
    date_format="%Y-%m-%d",
    customer_fmt="C{:05d}",
    invoice_fmt="INV-{:06d}",
    customer_start=10001,
    invoice_start=100001,
)

DS_GROCERY = Config(
    key="grocery_supermarket",
    filename="sample_grocery_supermarket.csv",
    seed=22,
    n_customers=420,
    invoices_by_tier={"low": (3, 9), "mid": (12, 22), "high": (26, 44)},
    tier_probs=(0.38, 0.42, 0.20),
    products=[
        ("Bananas 1kg", "Fresh Produce", "Fruit", 1.99, 9),
        ("Red Apples 1kg", "Fresh Produce", "Fruit", 3.49, 7),
        ("Strawberries 400g", "Fresh Produce", "Fruit", 3.99, 5),
        ("Avocados 2-Pack", "Fresh Produce", "Fruit", 2.99, 5),
        ("Tomatoes 500g", "Fresh Produce", "Vegetables", 2.49, 7),
        ("Baby Spinach 200g", "Fresh Produce", "Vegetables", 2.29, 5),
        ("Carrots 1kg", "Fresh Produce", "Vegetables", 1.49, 6),
        ("Onions 1kg", "Fresh Produce", "Vegetables", 1.69, 6),
        ("Potatoes 2kg", "Fresh Produce", "Vegetables", 3.29, 7),
        ("Ground Beef 500g", "Meat and Fish", "Meat", 5.49, 5),
        ("Chicken Breast 1kg", "Meat and Fish", "Meat", 8.99, 6),
        ("Salmon Fillets 2-Pack", "Meat and Fish", "Fish", 7.99, 3),
        ("Whole Milk 2L", "Dairy and Eggs", "Milk and Cream", 2.19, 10),
        ("Skimmed Milk 2L", "Dairy and Eggs", "Milk and Cream", 2.19, 5),
        ("Coffee Creamer", "Dairy and Eggs", "Milk and Cream", 3.19, 3),
        ("Cheddar Cheese 400g", "Dairy and Eggs", "Cheese and Eggs", 4.49, 6),
        ("Free Range Eggs 12", "Dairy and Eggs", "Cheese and Eggs", 3.79, 8),
        ("Greek Yogurt 500g", "Dairy and Eggs", "Cheese and Eggs", 2.89, 5),
        ("Butter 250g", "Dairy and Eggs", "Cheese and Eggs", 3.29, 6),
        ("Sliced Sandwich Bread", "Bakery", "Bread", 1.89, 9),
        ("Sourdough Loaf", "Bakery", "Bread", 3.99, 4),
        ("Burger Buns 6-Pack", "Bakery", "Bread", 2.29, 4),
        ("Butter Croissants 4-Pack", "Bakery", "Sweet Bakery", 3.49, 4),
        ("Spaghetti 500g", "Pantry", "Dry Goods", 1.59, 7),
        ("Basmati Rice 1kg", "Pantry", "Dry Goods", 3.19, 5),
        ("Breakfast Cereal", "Pantry", "Dry Goods", 3.99, 7),
        ("Rolled Oats 1kg", "Pantry", "Dry Goods", 2.99, 3),
        ("Tomato Pasta Sauce", "Pantry", "Sauces and Spreads", 2.49, 6),
        ("Olive Oil 500ml", "Pantry", "Sauces and Spreads", 6.49, 4),
        ("Peanut Butter 340g", "Pantry", "Sauces and Spreads", 3.19, 4),
        ("Strawberry Jam", "Pantry", "Sauces and Spreads", 2.59, 3),
        ("Potato Chips", "Pantry", "Snacks", 2.19, 6),
        ("Dark Chocolate Bar", "Pantry", "Snacks", 2.49, 5),
        ("Salted Crackers", "Pantry", "Snacks", 1.99, 3),
        ("Cola 2L", "Beverages", "Soft Drinks", 1.99, 7),
        ("Sparkling Water 6-Pack", "Beverages", "Soft Drinks", 3.99, 5),
        ("Orange Juice 1L", "Beverages", "Soft Drinks", 2.79, 5),
        ("Ground Coffee 227g", "Beverages", "Hot Drinks", 5.99, 6),
        ("Black Tea Bags 80", "Beverages", "Hot Drinks", 3.49, 5),
        ("Dish Soap", "Household", "Cleaning", 2.29, 6),
        ("Laundry Detergent", "Household", "Cleaning", 9.99, 4),
        ("Paper Towels 4-Roll", "Household", "Paper and Care", 4.99, 6),
        ("Toilet Paper 9-Roll", "Household", "Paper and Care", 6.49, 7),
        ("Hand Soap", "Household", "Paper and Care", 2.49, 4),
    ],
    bundles=[
        ("Whole Milk 2L", "Breakfast Cereal"),
        ("Spaghetti 500g", "Tomato Pasta Sauce"),
        ("Sliced Sandwich Bread", "Butter 250g"),
        ("Potato Chips", "Cola 2L"),
        ("Burger Buns 6-Pack", "Ground Beef 500g"),
        ("Ground Coffee 227g", "Coffee Creamer"),
        ("Peanut Butter 340g", "Strawberry Jam"),
        ("Tomatoes 500g", "Onions 1kg"),
        ("Chicken Breast 1kg", "Basmati Rice 1kg"),
        ("Dish Soap", "Paper Towels 4-Roll"),
    ],
    bundle_prob=0.50,
    extra_mean=2.4,
    qty_lambda={
        "Fresh Produce": 0.5,
        "Meat and Fish": 0.3,
        "Dairy and Eggs": 0.5,
        "Bakery": 0.3,
        "Pantry": 0.5,
        "Beverages": 0.6,
        "Household": 0.3,
    },
    seasonality=[1.00, 0.92, 0.97, 1.03, 1.02, 1.05, 1.08, 1.05, 0.98, 1.00, 1.08, 1.35],
    monthly_growth=0.003,
    extra_dim_values=["Downtown", "Riverside", "Hillcrest", "Lakeside"],
    id_prefix="GR",
    columns={
        "customer": "member_number",
        "invoice": "bill_id",
        "date": "purchase_date",
        "pid": "sku",
        "pname": "item_name",
        "cat": "department",
        "sub": "aisle",
        "qty": "qty",
        "price": "price",
        "sales": "amount",
        "extra": "store",
    },
    date_format="%d/%m/%Y",
    customer_fmt="{}",
    invoice_fmt="{}",
    customer_start=500100,
    invoice_start=7000001,
    weekend_boost=1.6,
)

DS_ELECTRONICS = Config(
    key="online_electronics",
    filename="sample_online_electronics.csv",
    seed=33,
    n_customers=900,
    invoices_by_tier={"low": (1, 3), "mid": (4, 8), "high": (9, 18)},
    tier_probs=(0.50, 0.35, 0.15),
    products=[
        ("Ultrabook 14 Inch", "Computing", "Laptops", 899.00, 3),
        ("Gaming Laptop 15 Inch", "Computing", "Laptops", 1349.00, 1.5),
        ("Budget Laptop 15 Inch", "Computing", "Laptops", 499.00, 3),
        ("Laptop Sleeve", "Computing", "Peripherals", 29.99, 4),
        ("4K Monitor 27 Inch", "Computing", "Peripherals", 329.00, 2),
        ("Wireless Keyboard and Mouse Combo", "Computing", "Peripherals", 49.99, 4),
        ("External SSD 1TB", "Computing", "Peripherals", 99.00, 4),
        ("Flagship Smartphone", "Mobile", "Smartphones", 999.00, 2),
        ("Mid-Range Smartphone", "Mobile", "Smartphones", 429.00, 4),
        ("Prepaid Smartphone", "Mobile", "Smartphones", 149.00, 3),
        ("Phone Case", "Mobile", "Phone Accessories", 19.99, 6),
        ("Screen Protector 2-Pack", "Mobile", "Phone Accessories", 12.99, 6),
        ("Fast Charger 30W", "Mobile", "Phone Accessories", 24.99, 5),
        ("Power Bank 20000mAh", "Mobile", "Phone Accessories", 39.99, 4),
        ("Wireless Earbuds", "Audio", "Headphones", 79.00, 5),
        ("Over-Ear Headphones", "Audio", "Headphones", 149.00, 3),
        ("Bluetooth Speaker", "Audio", "Home Audio", 59.00, 4),
        ("Soundbar", "Audio", "Home Audio", 199.00, 2),
        ("Turntable", "Audio", "Home Audio", 179.00, 1),
        ("Indoor Security Camera", "Smart Home", "Security", 49.00, 3),
        ("Video Doorbell", "Smart Home", "Security", 129.00, 2),
        ("Smart Bulb 4-Pack", "Smart Home", "Lighting and Plugs", 29.99, 4),
        ("Smart Plug 2-Pack", "Smart Home", "Lighting and Plugs", 22.99, 4),
        ("Smart Speaker", "Smart Home", "Assistants and Climate", 49.00, 3),
        ("Smart Thermostat", "Smart Home", "Assistants and Climate", 149.00, 1.5),
        ("Gaming Console", "Gaming", "Consoles", 449.00, 2.5),
        ("Handheld Console", "Gaming", "Consoles", 349.00, 1.5),
        ("Extra Controller", "Gaming", "Gaming Accessories", 59.00, 4),
        ("Gaming Headset", "Gaming", "Gaming Accessories", 69.00, 3),
        ("Gaming Mouse", "Gaming", "Gaming Accessories", 44.99, 3),
        ("Console Charging Dock", "Gaming", "Gaming Accessories", 29.99, 2),
    ],
    bundles=[
        ("Ultrabook 14 Inch", "Laptop Sleeve"),
        ("Budget Laptop 15 Inch", "Wireless Keyboard and Mouse Combo"),
        ("Flagship Smartphone", "Phone Case"),
        ("Flagship Smartphone", "Screen Protector 2-Pack"),
        ("Mid-Range Smartphone", "Phone Case"),
        ("Mid-Range Smartphone", "Fast Charger 30W"),
        ("Gaming Console", "Extra Controller"),
        ("Gaming Console", "Gaming Headset"),
        ("Smart Speaker", "Smart Bulb 4-Pack"),
        ("Video Doorbell", "Indoor Security Camera"),
        ("Wireless Earbuds", "Fast Charger 30W"),
        ("4K Monitor 27 Inch", "External SSD 1TB"),
    ],
    bundle_prob=0.62,
    extra_mean=0.25,
    qty_lambda={"Computing": 0.05, "Mobile": 0.15, "Audio": 0.1, "Smart Home": 0.25, "Gaming": 0.1},
    seasonality=[0.85, 0.80, 0.85, 0.90, 0.90, 0.95, 1.05, 0.95, 1.00, 1.10, 1.70, 1.60],
    monthly_growth=0.012,
    extra_dim_values=["Website", "Mobile App", "Marketplace", "Partner Store"],
    id_prefix="EL",
    columns={
        "customer": "Customer Id",
        "invoice": "Order Number",
        "date": "Order Date",
        "pid": "Item Code",
        "pname": "Item Description",
        "cat": "Segment",
        "sub": "Sub Segment",
        "qty": "Units",
        "price": "Price Per Unit",
        "sales": "Revenue",
        "extra": "Channel",
    },
    date_format="%m/%d/%Y %H:%M",
    customer_fmt="CUS-{:06d}",
    invoice_fmt="ORD-{:07d}",
    customer_start=100200,
    invoice_start=2400001,
)


DS_FASHION = Config(
    key="online_fashion",
    filename="sample_online_fashion.csv",
    seed=44,
    n_customers=1100,
    invoices_by_tier={"low": (1, 3), "mid": (4, 7), "high": (8, 15)},
    tier_probs=(0.55, 0.33, 0.12),
    products=[
        ("Classic White T-Shirt", "Tops", "T-Shirts", 19.90, 8),
        ("Graphic Print T-Shirt", "Tops", "T-Shirts", 24.90, 5),
        ("Oxford Button Shirt", "Tops", "Shirts", 49.90, 4),
        ("Linen Summer Shirt", "Tops", "Shirts", 44.90, 3),
        ("Merino Crew Sweater", "Tops", "Knitwear", 79.90, 3),
        ("Chunky Knit Cardigan", "Tops", "Knitwear", 69.90, 3),
        ("Slim Fit Jeans", "Bottoms", "Jeans", 69.90, 6),
        ("Straight Leg Jeans", "Bottoms", "Jeans", 64.90, 5),
        ("Stretch Chinos", "Bottoms", "Trousers", 54.90, 4),
        ("Pleated Midi Skirt", "Bottoms", "Skirts", 49.90, 3),
        ("Jersey Joggers", "Bottoms", "Trousers", 39.90, 4),
        ("Denim Jacket", "Outerwear", "Jackets", 89.90, 3),
        ("Bomber Jacket", "Outerwear", "Jackets", 99.90, 2),
        ("Wool Blend Coat", "Outerwear", "Coats", 189.00, 1.5),
        ("Quilted Puffer Coat", "Outerwear", "Coats", 149.00, 2),
        ("Waterproof Parka", "Outerwear", "Coats", 169.00, 1.5),
        ("Leather Sneakers", "Footwear", "Casual Shoes", 89.00, 5),
        ("Canvas Sneakers", "Footwear", "Casual Shoes", 49.00, 5),
        ("Running Shoes", "Footwear", "Sport Shoes", 99.00, 4),
        ("Chelsea Boots", "Footwear", "Boots", 119.00, 2),
        ("Ankle Boots", "Footwear", "Boots", 109.00, 2),
        ("Leather Belt", "Accessories", "Belts and Wallets", 29.90, 4),
        ("Slim Leather Wallet", "Accessories", "Belts and Wallets", 34.90, 3),
        ("Canvas Tote Bag", "Accessories", "Bags", 29.90, 4),
        ("Everyday Backpack", "Accessories", "Bags", 59.90, 3),
        ("Wool Scarf", "Accessories", "Scarves and Hats", 24.90, 3),
        ("Knit Beanie", "Accessories", "Scarves and Hats", 17.90, 3),
        ("Cotton Crew Socks 5-Pack", "Accessories", "Basics", 14.90, 7),
        ("Sunglasses Classic", "Accessories", "Eyewear", 39.90, 3),
    ],
    bundles=[
        ("Classic White T-Shirt", "Slim Fit Jeans"),
        ("Oxford Button Shirt", "Stretch Chinos"),
        ("Wool Scarf", "Knit Beanie"),
        ("Wool Blend Coat", "Wool Scarf"),
        ("Leather Sneakers", "Cotton Crew Socks 5-Pack"),
        ("Running Shoes", "Jersey Joggers"),
        ("Chelsea Boots", "Leather Belt"),
        ("Denim Jacket", "Graphic Print T-Shirt"),
        ("Leather Belt", "Slim Leather Wallet"),
        ("Quilted Puffer Coat", "Knit Beanie"),
    ],
    bundle_prob=0.5,
    extra_mean=0.7,
    qty_lambda={"Tops": 0.2, "Bottoms": 0.1, "Outerwear": 0.03, "Footwear": 0.05, "Accessories": 0.3},
    seasonality=[0.80, 0.75, 0.90, 1.00, 1.00, 0.95, 0.90, 0.95, 1.05, 1.15, 1.65, 1.70],
    monthly_growth=0.009,
    extra_dim_values=["United Kingdom", "Germany", "France", "Netherlands"],
    id_prefix="FS",
    columns={
        "customer": "user_id",
        "invoice": "order_ref",
        "date": "order_date",
        "pid": "style_code",
        "pname": "product_title",
        "cat": "product_type",
        "sub": "collection",
        "qty": "units",
        "price": "list_price",
        "sales": "line_total",
        "extra": "country",
    },
    date_format="%Y-%m-%dT%H:%M:%S",
    customer_fmt="U{:07d}",
    invoice_fmt="FS{:08d}",
    customer_start=2400100,
    invoice_start=30000001,
    return_rate=0.0,
)

DS_WHOLESALE = Config(
    key="wholesale_cafe_supplies",
    filename="sample_wholesale_cafe_supplies.csv",
    seed=55,
    n_customers=170,
    invoices_by_tier={"low": (5, 10), "mid": (14, 26), "high": (30, 50)},
    tier_probs=(0.40, 0.40, 0.20),
    products=[
        ("Espresso Beans 1kg Case of 6", "Coffee and Tea", "Coffee", 74.00, 8),
        ("Filter Coffee 1kg Case of 6", "Coffee and Tea", "Coffee", 62.00, 5),
        ("Decaf Beans 1kg Case of 6", "Coffee and Tea", "Coffee", 79.00, 2),
        ("Black Tea Bags 1000 Count", "Coffee and Tea", "Tea", 28.00, 5),
        ("Green Tea Bags 500 Count", "Coffee and Tea", "Tea", 22.00, 3),
        ("Whole Milk 1L Case of 12", "Dairy and Alternatives", "Milk", 14.50, 9),
        ("Oat Drink 1L Case of 12", "Dairy and Alternatives", "Milk", 21.00, 6),
        ("Barista Cream 1L Case of 6", "Dairy and Alternatives", "Cream", 12.50, 3),
        ("Butter Portions 200 Count", "Dairy and Alternatives", "Cream", 18.00, 3),
        ("Paper Cups 8oz 1000 Count", "Disposables", "Cups and Lids", 38.00, 8),
        ("Paper Cups 12oz 1000 Count", "Disposables", "Cups and Lids", 46.00, 7),
        ("Cup Lids 12oz 1000 Count", "Disposables", "Cups and Lids", 24.00, 7),
        ("Paper Napkins 5000 Count", "Disposables", "Napkins and Cutlery", 19.00, 6),
        ("Wooden Stirrers 5000 Count", "Disposables", "Napkins and Cutlery", 9.50, 5),
        ("Compostable Cutlery Set 500", "Disposables", "Napkins and Cutlery", 32.00, 3),
        ("Takeaway Boxes 250 Count", "Disposables", "Packaging", 27.00, 4),
        ("Paper Bags Large 500 Count", "Disposables", "Packaging", 21.00, 4),
        ("Vanilla Syrup 1L Case of 6", "Syrups and Sauces", "Syrups", 36.00, 4),
        ("Caramel Syrup 1L Case of 6", "Syrups and Sauces", "Syrups", 36.00, 4),
        ("Chocolate Sauce 2kg Case of 4", "Syrups and Sauces", "Sauces", 42.00, 3),
        ("Cocoa Powder 1kg Case of 6", "Syrups and Sauces", "Sauces", 44.00, 3),
        ("Sugar Sachets 2000 Count", "Pantry", "Sweeteners", 17.00, 6),
        ("Sweetener Sachets 1000 Count", "Pantry", "Sweeteners", 12.00, 3),
        ("Plain Flour 16kg Sack", "Pantry", "Baking", 15.00, 3),
        ("Frozen Croissants 60 Count", "Pantry", "Baking", 29.00, 4),
        ("Muffin Mix 5kg", "Pantry", "Baking", 16.50, 3),
        ("Surface Sanitiser 5L Case of 2", "Cleaning", "Hygiene", 23.00, 4),
        ("Washing Up Liquid 5L", "Cleaning", "Hygiene", 8.50, 4),
        ("Blue Roll 6 Pack", "Cleaning", "Paper", 25.00, 4),
        ("Bin Liners 500 Count", "Cleaning", "Paper", 19.50, 4),
        ("Espresso Machine Descaler 12 Pack", "Cleaning", "Equipment Care", 34.00, 2),
        ("Milk Jug Stainless 600ml", "Equipment", "Barista Tools", 11.50, 1.5),
        ("Tamper 58mm", "Equipment", "Barista Tools", 24.00, 1),
        ("Grinder Burr Set", "Equipment", "Spare Parts", 59.00, 0.8),
    ],
    bundles=[
        ("Paper Cups 8oz 1000 Count", "Cup Lids 12oz 1000 Count"),
        ("Paper Cups 12oz 1000 Count", "Cup Lids 12oz 1000 Count"),
        ("Espresso Beans 1kg Case of 6", "Whole Milk 1L Case of 12"),
        ("Espresso Beans 1kg Case of 6", "Sugar Sachets 2000 Count"),
        ("Paper Napkins 5000 Count", "Wooden Stirrers 5000 Count"),
        ("Takeaway Boxes 250 Count", "Paper Bags Large 500 Count"),
        ("Vanilla Syrup 1L Case of 6", "Caramel Syrup 1L Case of 6"),
        ("Surface Sanitiser 5L Case of 2", "Blue Roll 6 Pack"),
        ("Oat Drink 1L Case of 12", "Barista Cream 1L Case of 6"),
        ("Frozen Croissants 60 Count", "Butter Portions 200 Count"),
    ],
    bundle_prob=0.5,
    extra_mean=1.2,
    qty_lambda={"Coffee and Tea": 1.5, "Dairy and Alternatives": 2.5, "Disposables": 2.0, "Syrups and Sauces": 0.8, "Pantry": 1.2, "Cleaning": 1.0, "Equipment": 0.1},
    seasonality=[0.95, 0.95, 1.00, 1.05, 1.10, 1.10, 1.05, 1.00, 1.05, 1.05, 1.10, 1.00],
    monthly_growth=0.008,
    extra_dim_values=["North", "Central", "South", "Coastal"],
    id_prefix="WS",
    columns={
        "customer": "Account",
        "invoice": "Sales Order",
        "date": "Ship Date",
        "pid": "Item No",
        "pname": "Description",
        "cat": "Product Group",
        "sub": "Product Line",
        "qty": "Qty",
        "price": "Net Price",
        "sales": "Net Amount",
        "extra": "Region",
    },
    date_format="%d.%m.%Y",
    customer_fmt="AC-{:04d}",
    invoice_fmt="SO{:07d}",
    customer_start=1001,
    invoice_start=5500001,
    sep=";",
    decimal=",",
)


def month_weights(cfg: Config, join_idx: int) -> np.ndarray:
    weights = np.zeros(N_MONTHS)
    for i in range(N_MONTHS):
        month = (START + pd.DateOffset(months=i)).month
        weights[i] = cfg.seasonality[month - 1] * (1 + cfg.monthly_growth) ** i
    weights[:join_idx] = 0
    return weights / weights.sum()


def generate(cfg: Config) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    prods = pd.DataFrame(cfg.products, columns=["name", "cat", "sub", "price", "pop"])
    prods["pid"] = [f"{cfg.id_prefix}-{i + 1:03d}" for i in range(len(prods))]
    name_to_idx = {n: i for i, n in enumerate(prods["name"])}
    partners: dict[int, list[int]] = {i: [] for i in range(len(prods))}
    for a, b in cfg.bundles:
        partners[name_to_idx[a]].append(name_to_idx[b])
        partners[name_to_idx[b]].append(name_to_idx[a])

    cats = sorted(prods["cat"].unique())
    median_price = prods["price"].median()
    tiers = rng.choice(["low", "mid", "high"], size=cfg.n_customers, p=cfg.tier_probs)
    rows: list[dict] = []
    invoice_counter = cfg.invoice_start

    for c in range(cfg.n_customers):
        tier = tiers[c]
        # Most customers are active from the start; the rest join gradually.
        join_idx = 0 if rng.random() < 0.65 else int(rng.integers(1, 30))
        lo, hi = cfg.invoices_by_tier[tier]
        n_inv = int(rng.integers(lo, hi + 1))
        n_inv = max(1, int(round(n_inv * (N_MONTHS - join_idx) / N_MONTHS)))
        fav = rng.choice(cats, size=2, replace=False)
        extra_value = rng.choice(cfg.extra_dim_values)
        # Customer specific product preference
        w = prods["pop"].to_numpy(dtype=float).copy()
        for i, cat in enumerate(prods["cat"]):
            if cat == fav[0]:
                w[i] *= 3.0
            elif cat == fav[1]:
                w[i] *= 1.8
        if tier == "high":
            w = np.where(prods["price"].to_numpy() > median_price, w * 1.8, w)
        elif tier == "low":
            w = np.where(prods["price"].to_numpy() > median_price, w * 0.7, w)
        w = w / w.sum()

        mw = month_weights(cfg, join_idx)
        months_idx = rng.choice(N_MONTHS, size=n_inv, p=mw)
        for m_idx in months_idx:
            month_start = START + pd.DateOffset(months=int(m_idx))
            days_in_month = month_start.days_in_month
            day_weights = np.ones(days_in_month)
            if cfg.weekend_boost != 1.0:
                for d in range(days_in_month):
                    if (month_start + pd.Timedelta(days=d)).weekday() >= 5:
                        day_weights[d] = cfg.weekend_boost
            day_weights = day_weights / day_weights.sum()
            day = int(rng.choice(days_in_month, p=day_weights))
            hour = int(rng.integers(8, 22))
            minute = int(rng.integers(0, 60))
            stamp = month_start + pd.Timedelta(days=day, hours=hour, minutes=minute)
            if stamp > END + pd.Timedelta(days=1) - pd.Timedelta(minutes=1):
                stamp = END
            invoice_no = invoice_counter
            invoice_counter += 1

            chosen = [int(rng.choice(len(prods), p=w))]
            for p in list(chosen):
                for partner in partners[p]:
                    if rng.random() < cfg.bundle_prob * 0.75:
                        chosen.append(partner)
            n_extra = int(rng.poisson(cfg.extra_mean))
            for _ in range(n_extra):
                chosen.append(int(rng.choice(len(prods), p=w)))
            seen: list[int] = []
            for p in chosen:
                if p not in seen:
                    seen.append(p)

            for p in seen:
                cat = prods.at[p, "cat"]
                lam = cfg.qty_lambda.get(cat, 0.2) + (0.25 if tier == "high" else 0.0)
                qty = 1 + int(rng.poisson(lam))
                base_price = float(prods.at[p, "price"])
                drift = 1 + 0.002 * m_idx  # gentle price inflation
                price = base_price * drift
                if rng.random() < 0.15:
                    price *= rng.uniform(0.85, 0.95)  # promotions
                price = round(price, 2)
                rows.append(
                    {
                        "customer": cfg.customer_fmt.format(cfg.customer_start + c),
                        "invoice": cfg.invoice_fmt.format(invoice_no),
                        "date": stamp,
                        "pid": prods.at[p, "pid"],
                        "pname": prods.at[p, "name"],
                        "cat": cat,
                        "sub": prods.at[p, "sub"],
                        "qty": qty,
                        "price": price,
                        "sales": round(qty * price, 2),
                        "extra": extra_value,
                    }
                )
                if cfg.return_rate > 0 and rng.random() < cfg.return_rate:
                    # A return: a negative row booked a few days later under its own reference.
                    back_qty = int(rng.integers(1, qty + 1))
                    back_stamp = min(stamp + pd.Timedelta(days=int(rng.integers(3, 21))), END)
                    rows.append(
                        {
                            "customer": cfg.customer_fmt.format(cfg.customer_start + c),
                            "invoice": cfg.invoice_fmt.format(invoice_no) + "R",
                            "date": back_stamp,
                            "pid": prods.at[p, "pid"],
                            "pname": prods.at[p, "name"],
                            "cat": cat,
                            "sub": prods.at[p, "sub"],
                            "qty": -back_qty,
                            "price": price,
                            "sales": round(-back_qty * price, 2),
                            "extra": extra_value,
                        }
                    )

    df = pd.DataFrame(rows).sort_values(["date", "invoice", "pid"]).reset_index(drop=True)
    df["date"] = df["date"].dt.strftime(cfg.date_format)
    df = df[["customer", "invoice", "date", "pid", "pname", "cat", "sub", "qty", "price", "sales", "extra"]]
    df.columns = [cfg.columns[c] for c in df.columns]
    return df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for cfg in (DS_OFFICE, DS_GROCERY, DS_ELECTRONICS, DS_FASHION, DS_WHOLESALE):
        df = generate(cfg)
        path = OUT_DIR / cfg.filename
        df.to_csv(path, index=False, sep=cfg.sep, decimal=cfg.decimal)
        inv_col = cfg.columns["invoice"]
        sizes = df.groupby(inv_col).size()
        print(
            f"{cfg.filename}: {len(df):,} rows, {df[cfg.columns['customer']].nunique()} customers, "
            f"{df[inv_col].nunique():,} invoices, avg basket {sizes.mean():.2f}, "
            f"multi-item baskets {(sizes > 1).mean():.0%}, size {path.stat().st_size / 1e6:.2f} MB"
        )


if __name__ == "__main__":
    main()
