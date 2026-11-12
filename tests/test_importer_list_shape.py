import json, zipfile
from pathlib import Path
from src.instagram_lab.importer import import_export

def test_list_root_liked(tmp_path):
    zip_path = tmp_path / "listroot.zip"
    payload = [
        {"title": "user_a", "string_list_data": [{"href": "https://www.instagram.com/p/X1/", "timestamp": 1}]},
        {"title": "user_b", "string_list_data": [{"href": "https://www.instagram.com/p/X2/", "timestamp": 2}]},
    ]
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("liked_posts.json", json.dumps(payload))

    posts = import_export(zip_path)
    assert len(posts) == 2
    assert {p.interaction for p in posts} == {"liked"}
    assert {p.creator for p in posts} == {"user_a", "user_b"}
