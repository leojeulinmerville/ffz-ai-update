from app.services.whatsapp_sender import normalize_fr_phone


def test_normalize_fr_phone_variants():
    assert normalize_fr_phone("0608123456") == "+33608123456"
    assert normalize_fr_phone("+33608123456") == "+33608123456"
    assert normalize_fr_phone("33 6 08 12 34 56") == "+33608123456"
    assert normalize_fr_phone("708123456") == "+33708123456"
