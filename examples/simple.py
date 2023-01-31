from shopback_sdk.products import ClientSDK, ProductData

c = ClientSDK("session_id")

attachment_ids = c.upload_urls(
    [
        "https://images.ctfassets.net/hrltx12pl8hq/3j5RylRv1ZdswxcBaMi0y7/b84fa97296bd2350db6ea194c0dce7db/Music_Icon.jpg"
    ]
)

product_id = c.upload_product_and_return_id(
    ProductData(
        project_id=273,
        category_name="test",
        name="test",
        description="test",
        price=20,
        attachment_ids=attachment_ids,
        external_id="test_external_id",
    )
)
print(product_id)
