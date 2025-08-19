from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

Point = Tuple[int, int]

@dataclass
class HandLandmarks:
    # 21 landmarks per mano, in pixel coords sull'immagine
    points: List[Point]
    handedness: str  # "Left" | "Right"
    score: float

@dataclass
class FrameData:
    frame_bgr: np.ndarray
    hands: List[HandLandmarks]

@dataclass
class GestureEvent:
    name: str  # "heart" | "wave"
    confidence: float
    hands_involved: int  # 1 o 2
