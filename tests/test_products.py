from shopback_sdk.products import ClientSDK


def test_ok():
    s = ClientSDK("", "")
    assert s
