def test_item_base_dimensions(item_loader):
    """Test that all items within one base have the same dimension."""
    bases = {}

    # Group items by base
    for item in item_loader:
        bases.setdefault(item.base, [])
        bases[item.base].append(item)

    for base, items in bases.items():
        msg = f"Items from base '{base}' don't have the same dimensions"
        assert len({(item.width, item.height) for item in items}) == 1, msg
