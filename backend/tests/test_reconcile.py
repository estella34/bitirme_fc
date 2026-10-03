import pytest

from envanter.models import ObservationStatus as S
from envanter.services.reconcile import reconcile


@pytest.mark.parametrize(
    ("codes", "expected", "boxes", "status"),
    [
        ({"a", "b"}, {"a", "b"}, None, S.VERIFIED),
        ({"a", "b"}, {"a", "b"}, 2, S.VERIFIED),
        ({"a"}, {"a", "b"}, 1, S.CONFLICT),  # koli kayıp (sayım doğruluyor)
        ({"a"}, {"a", "b"}, 2, S.UNREADABLE),  # koli var ama okunamadı
        ({"a"}, {"a", "b"}, None, S.UNREADABLE),  # sayım yok → kesin konuşma
        ({"a", "x"}, {"a", "b"}, 2, S.CONFLICT),  # yanlış koli
        ({"x"}, set(), 1, S.CONFLICT),  # boş olması gereken gözde koli
        (set(), set(), 0, S.EMPTY),
        (set(), {"a"}, 0, S.CONFLICT),  # beklenen koli yok, göz boş
        (set(), {"a"}, 1, S.UNREADABLE),
        (set(), set(), None, S.UNREADABLE),  # boş olduğu doğrulanamadı
        ({"a"}, None, None, S.OBSERVED),  # stok bilgisi yok
        ({"a", "b"}, {"a", "b"}, 3, S.CONFLICT),  # fazladan okunamayan koli
    ],
)
def test_reconcile(codes, expected, boxes, status):
    assert reconcile(codes, expected, boxes).status == status


def test_details_are_reported():
    v = reconcile({"a", "x"}, {"a", "b"}, 2)
    assert v.missing == ["b"]
    assert v.unexpected == ["x"]
    assert v.review.value == "pending"


def test_verified_needs_no_review():
    assert reconcile({"a"}, {"a"}, 1).review.value == "none"
