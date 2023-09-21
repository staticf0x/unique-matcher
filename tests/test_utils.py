from unique_matcher.matcher import utils


def test_normalize_item_name():
    assert utils.normalize_item_name("Bones of Ullr") == "Bones_of_Ullr"
    assert utils.normalize_item_name("Three-step Assault") == "Three-step_Assault"
    assert utils.normalize_item_name("Ungil's Harmony") == "Ungils_Harmony"
