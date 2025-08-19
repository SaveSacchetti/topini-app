from __future__ import annotations
from typing import List

import cv2
import numpy as np
import mediapipe as mp

from src.utils.types import HandLandmarks

mp_hands = mp.solutions.hands


class HandTracker:
    def __init__(self, max_num_hands: int = 2, detection_confidence: float = 0.6, tracking_confidence: float = 0.6):
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
            model_complexity=1,
        )
        self._drawer = mp.solutions.drawing_utils
        self._drawer_style = mp.solutions.drawing_styles

    def process(self, frame_bgr: np.ndarray) -> List[HandLandmarks]:            
        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.hands.process(frame_rgb)
        hands: List[HandLandmarks] = []
        if result.multi_hand_landmarks:
            for idx, (lm, handedness) in enumerate(zip(result.multi_hand_landmarks, result.multi_handedness)):
                pts = []
                for p in lm.landmark:
                    x = int(p.x * w)
                    y = int(p.y * h)
                    pts.append((x, y))
                label = handedness.classification[0].label  # 'Left' or 'Right'
                score = handedness.classification[0].score
                hands.append(HandLandmarks(points=pts, handedness=label, score=score))
        return hands

    def draw(self, frame_bgr: np.ndarray, hands: List[HandLandmarks]) -> np.ndarray:
        # For drawing we re-run mediapipe to access landmark connections; alternatively draw simple circles/lines.
        # Here we'll draw simple circles and lines for performance.
        out = frame_bgr.copy()
        for hand in hands:
            # draw points
            for (x, y) in hand.points:
                cv2.circle(out, (x, y), 3, (0, 255, 0), -1)
            # draw some key connections (approx subset)
            def line(i, j):
                cv2.line(out, hand.points[i], hand.points[j], (0, 200, 0), 2)
            # palm
            palm = [(0,1),(1,2),(2,5),(5,9),(9,13),(13,17),(17,0)]
            for a,b in palm:
                line(a,b)
            # fingers chains
            chains = [
                [0, 1, 2, 3, 4],
                [0, 5, 6, 7, 8],
                [0, 9,10,11,12],
                [0,13,14,15,16],
                [0,17,18,19,20],
            ]
            for chain in chains:
                for i in range(len(chain)-1):
                    line(chain[i], chain[i+1])
        return out

    def close(self):
        self.hands.close()
