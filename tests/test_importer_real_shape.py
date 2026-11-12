import json, zipfile
from src.instagram_lab.importer import import_export


def test_new_label_values_shape(tmp_path):
    payload = [
        {"timestamp": 1794492442, "media": [], "fbid": "123",
         "label_values": [
            {"label": "URL", "value": "https://www.instagram.com/reel/AAA/",
             "href": "https://www.instagram.com/reel/AAA/"},
            {"label": "Caption", "value": "some caption"},
            {"label": "Title", "value": ""},
            {"dict": [{"dict": [{"label": "Name", "value": "creator_a"}]}]},
         ]},
        {"timestamp": 1794493000, "media": [], "fbid": "456",
         "label_values": [
            {"label": "URL", "value": "https://www.instagram.com/p/BBB/"},
            {"dict": [{"dict": [{"label": "Name", "value": "creator_b"}]}]},
         ]},
    ]
    zp = tmp_path / "real.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        zf.writestr("liked_posts.json", json.dumps(payload))

    posts = import_export(zp)
    assert len(posts) == 2
    assert {p.interaction for p in posts} == {"liked"}
    assert {p.creator for p in posts} == {"creator_a", "creator_b"}
    assert {p.url for p in posts} == {
        "https://www.instagram.com/reel/AAA/",
        "https://www.instagram.com/p/BBB/",
    }
