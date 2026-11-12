import json, zipfile
from pathlib import Path
from src.instagram_lab.importer import import_export

FIXTURE = Path(__file__).parent / "fixtures" / "sample_export.json"


def _build_zip(tmp_path, data):
    """Helper: build a ZIP with the two files the importer looks for."""
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(
            "liked_posts.json",
            json.dumps({"likes_media_likes": data["likes_media_likes"]}),
        )
        zf.writestr(
            "saved_posts.json",
            json.dumps({"saved_posts": data["saved_posts"]}),
        )
    return zip_path


def test_import_finds_both(tmp_path):
    data = json.loads(FIXTURE.read_text())
    posts = import_export(_build_zip(tmp_path, data))

    # Order-independent checks
    assert len(posts) == 2
    assert {p.interaction for p in posts} == {"saved", "liked"}
    assert all(p.url.startswith("https://") for p in posts)
    assert all(p.creator.startswith("fake_creator_") for p in posts)


def test_import_maps_interaction_to_creator(tmp_path):
    data = json.loads(FIXTURE.read_text())
    posts = import_export(_build_zip(tmp_path, data))

    by_interaction = {p.interaction: p for p in posts}
    assert by_interaction["liked"].creator == "fake_creator_1"
    assert by_interaction["saved"].creator == "fake_creator_2"
