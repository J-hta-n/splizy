from src.lib.receipt_parser.model import Receipt

mock_parsed_receipt: Receipt = Receipt(
    **{
        "items": [
            {
                "name": "Hong Kong Milk Tea (Cold)",
                "quantity": 4,
                "subtotal": 14.00,
            },
            {
                "name": "Honey Sea Coconut with Longan",
                "quantity": 1,
                "subtotal": 3.50,
            },
            {"name": "BBQ Pork Rice", "quantity": 1, "subtotal": 3.50},
            {"name": "Char Siew Bao", "quantity": 1, "subtotal": 2.90},
            {"name": "Red Bean Paste Bao", "quantity": 1, "subtotal": 2.10},
            {"name": "Mango with Pomelo & Sago", "quantity": 1, "subtotal": 4.80},
            {"name": "Hong Kong Style Milk Tea", "quantity": 1, "subtotal": 6.80},
            {"name": "Red Bean Paste Pancake", "quantity": 1, "subtotal": 4.80},
            {"name": "Grass Jelly Drink", "quantity": 1, "subtotal": 2.70},
            {"name": "Yam Paste w/ Ginkgo Nut", "quantity": 1, "subtotal": 4.50},
            {
                "name": "Sweet Potato Salted Egg Custard Ball",
                "quantity": 1,
                "subtotal": 3.80,
            },
            {"name": "Siew Mai", "quantity": 3, "subtotal": 8.70},
            {"name": "Har Gow", "quantity": 3, "subtotal": 12.60},
            {"name": "Rice Roll with Prawn", "quantity": 1, "subtotal": 5.00},
            {
                "name": "Bean Curd Prawn Roll",
                "quantity": 3,
                "subtotal": 12.60,
            },
            {"name": "Fried Prawn Dumpling", "quantity": 1, "subtotal": 5.40},
            {"name": "Water Chestnut Drink", "quantity": 1, "subtotal": 2.70},
            {"name": "Xiao Long Bao", "quantity": 1, "subtotal": 5.90},
            {"name": "Spring Roll", "quantity": 1, "subtotal": 2.80},
            {
                "name": "Salted Egg Yolk Custard Bao (Fried)",
                "quantity": 1,
                "subtotal": 6.00,
            },
            {"name": "Glutinous Rice with Chicken", "quantity": 1, "subtotal": 3.50},
            {"name": "Portuguese Egg Tart", "quantity": 1, "subtotal": 4.40},
            {
                "name": "Prawn Hor Fun in Creamy Egg Sauce",
                "quantity": 1,
                "subtotal": 8.80,
            },
            {"name": "Barley Drink", "quantity": 1, "subtotal": 2.70},
        ],
        "subtotal": 134.50,
        "service_charge": 13.45,
        "gst": 13.32,
        "total": 161.27,
        "currency": "SGD",
    }
)
