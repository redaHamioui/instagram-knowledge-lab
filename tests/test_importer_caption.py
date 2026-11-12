import json
import zipfile

from src.instagram_lab.importer import import_export


# Build a ZIP containing one new-format liked post with its caption for importer testing.
def test_importer_extracts_caption_and_hashtags(tmp_path):
    payload = [{
        "timestamp": 1794492442,
        "media": [],
        "fbid": "caption-test",
        "label_values": [
            {"label": "URL", "value": "https://www.instagram.com/reel/T1/"},
            {"label": "Caption", "value": "Cool #Python tip #tips"},
            {"dict": [{"dict": [{"label": "Name", "value": "someone"}]}]},
        ],
    }]
    zip_path = tmp_path / "caption-export.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("liked_posts.json", json.dumps(payload))

    posts = import_export(zip_path)

    assert len(posts) == 1
    post = posts[0]
    assert post.url == "https://www.instagram.com/reel/T1/"
    assert post.creator == "someone"
    assert post.caption == "Cool #Python tip #tips"
    assert post.hashtags == "python,tips"
