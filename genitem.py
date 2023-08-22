import sys

from loguru import logger

from unique_matcher.generator import ItemGenerator

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level:7s}</level> | {message}",
    level="DEBUG",
    colorize=True,
)


generator = ItemGenerator()

for i in range(1, 7):
    item = generator.generate_image("templates/Bramblejack_inventory_icon.png", i)
    item.save(f"generated/Bramblejack_{i}s.png")
