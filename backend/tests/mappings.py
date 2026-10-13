"""Correct column choices for each bundled sample, used by the tests."""

SAMPLES = {
    "office-home-retail": {
        "file": "sample_office_home_retail.csv",
        "cols": {
            "customer": "CustomerID", "invoice": "InvoiceNo", "date": "InvoiceDate",
            "pid": "ProductID", "pname": "ProductName", "cat": "Category", "sub": "SubCategory",
            "qty": "Quantity", "price": "UnitPrice", "sales": "Sales", "extra": "Region",
        },
        "filter_value": "Furniture",
        "additional_value": "North",
    },
    "grocery-supermarket": {
        "file": "sample_grocery_supermarket.csv",
        "cols": {
            "customer": "member_number", "invoice": "bill_id", "date": "purchase_date",
            "pid": "sku", "pname": "item_name", "cat": "department", "sub": "aisle",
            "qty": "qty", "price": "price", "sales": "amount", "extra": "store",
        },
        "filter_value": "Dairy and Eggs",
        "additional_value": "Downtown",
    },
    "online-electronics": {
        "file": "sample_online_electronics.csv",
        "cols": {
            "customer": "Customer Id", "invoice": "Order Number", "date": "Order Date",
            "pid": "Item Code", "pname": "Item Description", "cat": "Segment", "sub": "Sub Segment",
            "qty": "Units", "price": "Price Per Unit", "sales": "Revenue", "extra": "Channel",
        },
        "filter_value": "Mobile",
        "additional_value": "Website",
    },
    "online-fashion": {
        "file": "sample_online_fashion.csv",
        "cols": {
            "customer": "user_id", "invoice": "order_ref", "date": "order_date",
            "pid": "style_code", "pname": "product_title", "cat": "product_type", "sub": "collection",
            "qty": "units", "price": "list_price", "sales": "line_total", "extra": "country",
        },
        "filter_value": "Tops",
        "additional_value": "Germany",
    },
    "wholesale-cafe-supplies": {
        "file": "sample_wholesale_cafe_supplies.csv",
        "cols": {
            "customer": "Account", "invoice": "Sales Order", "date": "Ship Date",
            "pid": "Item No", "pname": "Description", "cat": "Product Group", "sub": "Product Line",
            "qty": "Qty", "price": "Net Price", "sales": "Net Amount", "extra": "Region",
        },
        "filter_value": "Coffee and Tea",
        "additional_value": "North",
    },
}


def clv_params(c):
    return {
        "customer_id": c["customer"], "invoice_id": c["invoice"], "invoice_date": c["date"],
        "quantity": c["qty"], "unit_price": c["price"],
    }


def recommendation_params(c):
    return {
        "product_id": c["pid"], "product_name": c["pname"], "sales": c["sales"],
        "category": c["cat"], "sub_category": c["sub"], "quantity": c["qty"], "customer_id": c["customer"],
    }


def basket_params(c):
    return {"member_number": c["customer"], "date": c["date"], "product_name": c["pname"]}


def forecast_params(c, filter_value="__ALL__", additional=None, periods=6, use_additional=False):
    p = {
        "sales": c["sales"], "date": c["date"], "filter_column": c["cat"],
        "filter_value": filter_value, "periods": periods,
    }
    if use_additional:
        p["additional_column"] = c["extra"]
        p["additional_value"] = additional if additional is not None else "__ALL__"
    return p
