#!/usr/bin/env python3
import os
import time

import pyscreenshot

from unique_matcher.constants import QUEUE_DIR

os.makedirs(QUEUE_DIR, exist_ok=True)

filename = QUEUE_DIR / f"{time.strftime('%Y-%m-%d-%H-%M-%S')}.png"

image = pyscreenshot.grab()
image.save(filename)
