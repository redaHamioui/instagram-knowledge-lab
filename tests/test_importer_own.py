import json
import zipfile

from src.instagram_lab.importer import import_export


def test_import_own_posts_default_and_all_mode(tmp_path):
    zip_path = tmp_path / "own-and-saved.zip"
    own = [{"media": [{
        "uri": "media/posts/a.jpg",
        "creation_timestamp": 1704067200,
        "title": "My own post about #python",
    }]}]
    saved = [{
        "timestamp": 1704067200,
        "label_values": [
            {"label": "URL", "value": "https://www.instagram.com/p/SAVED/"},
            {"dict": [{"dict": [{"label": "Name", "value": "someone"}]}]},
        ],
    }]
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "your_instagram_activity/content/posts_1.json", json.dumps(own)
        )
        archive.writestr(
            "your_instagram_activity/saved/saved_posts.json", json.dumps(saved)
        )

    posts_own = import_export(zip_path, mode="own")
    assert len(posts_own) == 1
    assert posts_own[0].interaction == "own"
    assert "python" in (posts_own[0].hashtags or "")

    posts_all = import_export(zip_path, mode="all")
    assert len(posts_all) == 2
    assert {post.interaction for post in posts_all} == {"own", "saved"}
