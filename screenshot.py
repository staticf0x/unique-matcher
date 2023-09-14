#!/usr/bin/env python3
import time

import pyscreenshot

from unique_matcher.constants import QUEUE_DIR

filename = QUEUE_DIR / f"{time.strftime('%Y-%m-%d-%H-%M-%S')}.png"

image = pyscreenshot.grab()
image.save(filename)
