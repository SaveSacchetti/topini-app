from __future__ import annotations
from typing import List, Optional, Tuple, Deque, Any
import math
from collections import deque
import time

from src.utils.types import HandLandmarks, GestureEvent

Point = Tuple[int, int]


class GestureDetector:
    """
    Gesti supportati:
    - heart: due mani formano un cuore (indici vicini + pollici vicini) con indici sopra i pollici; richiede persistenza e cooldown.
    - wave: saluto con oscillazione del polso o del palmo; richiede mano aperta e palmo ragionevolmente visibile; supporta sia traslazione sia rotazione.
    """

    def __init__(self):
        # ~0.9s finestre temporali per analisi movimento
        self.history_left_side: Deque[Tuple[float, Point]] = deque(maxlen=24)   # (timestamp, (x,y))
        self.history_right_side: Deque[Tuple[float, Point]] = deque(maxlen=24)
        # storia orientamento palmo (angolo in gradi della linea 5->17)
        self.orient_left_side: Deque[Tuple[float, float]] = deque(maxlen=24)    # (timestamp, angle_deg)
        self.orient_right_side: Deque[Tuple[float, float]] = deque(maxlen=24)
        # seconda traccia orientamento: polso -> middle MCP(9)
        self.orient2_left_side: Deque[Tuple[float, float]] = deque(maxlen=24)
        self.orient2_right_side: Deque[Tuple[float, float]] = deque(maxlen=24)

        # Debounce / persistenza
        self._heart_ok_count = 0
        self._heart_required_frames = 6  # ~180ms

        # Cooldown per evitare multi trigger
        self._cooldown_until_wave = 0.0
        self._cooldown_until_heart = 0.0
        self._cooldown_until_middle_finger = 0.0
        self._cooldown_wave_s = 1.0
        self._cooldown_heart_s = 1.0
        self._cooldown_middle_finger_s = 1.0

    @staticmethod
    def _distance(a: Point, b: Point) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def _mean_x(hand: HandLandmarks) -> float:
        return sum(p[0] for p in hand.points) / len(hand.points)

    @staticmethod
    def _palm_size(hand: HandLandmarks) -> float:
        # uso distanza wrist(0) -> middle_tip(12) come scala indicativa
        return math.hypot(hand.points[12][0]-hand.points[0][0], hand.points[12][1]-hand.points[0][1])

    def _extended_fingers_count(self, hand: HandLandmarks) -> int:
        wrist = hand.points[0]
        # (tip_index, mcp_index) per index, middle, ring, pinky
        pairs = [(8, 5), (12, 9), (16, 13), (20, 17)]
        scale = max(40.0, self._palm_size(hand))
        margin = 0.05 * scale
        count = 0
        for tip_i, mcp_i in pairs:
            tip_d = self._distance(hand.points[tip_i], wrist)
            mcp_d = self._distance(hand.points[mcp_i], wrist)
            if tip_d > (mcp_d + margin):
                count += 1
        return count

    def _palm_width(self, hand: HandLandmarks) -> float:
        # distanza tra index_mcp(5) e pinky_mcp(17)
        p5, p17 = hand.points[5], hand.points[17]
        return self._distance(p5, p17)

    def _finger_spread_ratio(self, hand: HandLandmarks) -> float:
        # distanza tra index_tip(8) e pinky_tip(20) in rapporto alla scala
        scale = max(1.0, self._palm_size(hand))
        return self._distance(hand.points[8], hand.points[20]) / scale

    def _is_hand_open(self, hand: HandLandmarks) -> bool:
        # mano apertamente aperta: almeno 3 dita estese
        return self._extended_fingers_count(hand) >= 3

    def _is_palm_visible(self, hand: HandLandmarks) -> bool:
        size = self._palm_size(hand)
        width = self._palm_width(hand)
        spread = self._finger_spread_ratio(hand)
        # condizione più semplice e permissiva: palmo abbastanza largo o dita abbastanza aperte
        min_w = max(24.0, 0.22 * size)
        min_spread = 0.22
        return (width >= min_w) or (spread >= min_spread)

    def detect(self, hands: List[HandLandmarks]) -> Optional[GestureEvent]:
        now = time.time()
        sorted_hands = sorted(hands, key=self._mean_x) if hands else []

        # MIDDLE FINGER (priorità alta per intercettare il gesto offensivo)
        middle_finger_conf, middle_finger_hands = self._detect_middle_finger(sorted_hands)
        if middle_finger_conf >= 0.85 and middle_finger_hands > 0 and now >= self._cooldown_until_middle_finger:
            self._cooldown_until_middle_finger = now + self._cooldown_middle_finger_s
            return GestureEvent(name='middle_finger', confidence=middle_finger_conf, hands_involved=middle_finger_hands)

        # WAVE
        wave_conf, wave_hands = self._detect_wave_sides(sorted_hands)
        if wave_conf >= 0.85 and wave_hands > 0 and now >= self._cooldown_until_wave:
            self._cooldown_until_wave = now + self._cooldown_wave_s
            return GestureEvent(name='wave', confidence=wave_conf, hands_involved=wave_hands)

        # HEART (richiede persistenza qualche frame)
        heart_conf = self._detect_heart_any(sorted_hands)
        if heart_conf >= 0.92:
            self._heart_ok_count += 1
        else:
            self._heart_ok_count = 0
        if self._heart_ok_count >= self._heart_required_frames and now >= self._cooldown_until_heart:
            self._heart_ok_count = 0
            self._cooldown_until_heart = now + self._cooldown_heart_s
            return GestureEvent(name='heart', confidence=heart_conf, hands_involved=2)

        return None

    def _push_time_window(self, hist: Deque[Tuple[float, Any]], now: float, item: Any, window_s: float = 0.9):
        hist.append((now, item))
        while hist and (now - hist[0][0]) > window_s:
            hist.popleft()

    def _angle_deg(self, a: Point, b: Point) -> float:
        # angolo in gradi della linea a->b
        dy = b[1] - a[1]
        dx = b[0] - a[0]
        return math.degrees(math.atan2(dy, dx))

    def _unwrap(self, angles: List[float]) -> List[float]:
        # evita salti +/-180°
        if not angles:
            return angles
        unwrapped = [angles[0]]
        for ang in angles[1:]:
            prev = unwrapped[-1]
            diff = ang - prev
            while diff > 180:
                ang -= 360
                diff = ang - prev
            while diff < -180:
                ang += 360
                diff = ang - prev
            unwrapped.append(ang)
        return unwrapped

    def _detect_wave_sides(self, sorted_hands: List[HandLandmarks]):
        conf = 0.0
        involved = 0
        now = time.time()

        left_hand = sorted_hands[0] if len(sorted_hands) >= 1 else None
        right_hand = sorted_hands[1] if len(sorted_hands) >= 2 else None

        for hand, pos_hist, ang_hist, ang2_hist in (
            (left_hand, self.history_left_side, self.orient_left_side, self.orient2_left_side),
            (right_hand, self.history_right_side, self.orient_right_side, self.orient2_right_side),
        ):
            if not hand:
                pos_hist.clear(); ang_hist.clear(); ang2_hist.clear()
                continue

            # gating: mano aperta e palmo visibile
            if not (self._is_hand_open(hand) and self._is_palm_visible(hand)):
                pos_hist.clear(); ang_hist.clear(); ang2_hist.clear()
                continue

            wrist = hand.points[0]
            p5, p17 = hand.points[5], hand.points[17]
            p9 = hand.points[9]
            ang = self._angle_deg(p5, p17)
            ang2 = self._angle_deg(wrist, p9)

            self._push_time_window(pos_hist, now, wrist)
            self._push_time_window(ang_hist, now, ang)
            self._push_time_window(ang2_hist, now, ang2)

            contributed = False

            # 1) Traslazione laterale del polso (leggermente permissiva)
            if len(pos_hist) >= 10:
                times = [t for (t, _) in pos_hist]
                xs = [p[0] for (_, p) in pos_hist]
                ys = [p[1] for (_, p) in pos_hist]
                dt = times[-1] - times[0]
                if dt > 0:
                    diffs = [xs[i+1] - xs[i] for i in range(len(xs)-1)]
                    thr = 2.5
                    signs = [1 if d > thr else (-1 if d < -thr else 0) for d in diffs]
                    comp = [s for s in signs if s != 0]
                    changes = sum(1 for i in range(len(comp)-1) if comp[i] != comp[i+1])
                    amp_x = max(xs) - min(xs)
                    mean_y = sum(ys)/len(ys)
                    var_y = sum((y-mean_y)**2 for y in ys)/len(ys)
                    std_y = math.sqrt(var_y)

                    scale = self._palm_size(hand)
                    min_amp = max(24.0, 0.24 * scale)
                    avg_speed = sum(abs(d) for d in diffs) / dt
                    min_speed = max(45.0, 0.50 * min_amp)

                    if changes >= 3 and amp_x >= min_amp and std_y <= 1.0 * amp_x and avg_speed >= min_speed:
                        conf_here = min(1.0, 0.68 + 0.06*changes + amp_x/(5.0*min_amp))
                        conf = max(conf, conf_here)
                        contributed = True

            # 2) Oscillazione orientamento palmo 5->17
            if len(ang_hist) >= 10:
                times = [t for (t, _) in ang_hist]
                angs = [a for (_, a) in ang_hist]
                dt = times[-1] - times[0]
                if dt > 0:
                    unwrap = self._unwrap(angs)
                    diffs = [unwrap[i+1] - unwrap[i] for i in range(len(unwrap)-1)]
                    athr = 5.0
                    signs = [1 if d > athr else (-1 if d < -athr else 0) for d in diffs]
                    comp = [s for s in signs if s != 0]
                    changes = sum(1 for i in range(len(comp)-1) if comp[i] != comp[i+1])
                    amp_a = max(unwrap) - min(unwrap)
                    avg_aspeed = sum(abs(d) for d in diffs) / dt

                    min_amp_a = 16.0
                    min_aspeed = 40.0

                    if changes >= 3 and amp_a >= min_amp_a and avg_aspeed >= min_aspeed:
                        conf_here = min(1.0, 0.68 + 0.05*changes + amp_a/90.0)
                        conf = max(conf, conf_here)
                        contributed = True

            # 3) Oscillazione orientamento polso->middle MCP (0->9)
            if len(ang2_hist) >= 10:
                times = [t for (t, _) in ang2_hist]
                angs = [a for (_, a) in ang2_hist]
                dt = times[-1] - times[0]
                if dt > 0:
                    unwrap = self._unwrap(angs)
                    diffs = [unwrap[i+1] - unwrap[i] for i in range(len(unwrap)-1)]
                    athr = 5.0
                    signs = [1 if d > athr else (-1 if d < -athr else 0) for d in diffs]
                    comp = [s for s in signs if s != 0]
                    changes = sum(1 for i in range(len(comp)-1) if comp[i] != comp[i+1])
                    amp_a = max(unwrap) - min(unwrap)
                    avg_aspeed = sum(abs(d) for d in diffs) / dt

                    min_amp_a = 14.0
                    min_aspeed = 36.0

                    if changes >= 3 and amp_a >= min_amp_a and avg_aspeed >= min_aspeed:
                        conf_here = min(1.0, 0.68 + 0.05*changes + amp_a/90.0)
                        conf = max(conf, conf_here)
                        contributed = True

            if contributed:
                involved += 1

        return conf, (involved if conf > 0 else 0)

    def _detect_heart_any(self, sorted_hands: List[HandLandmarks]) -> float:
        if len(sorted_hands) < 2:
            return 0.0
        left = sorted_hands[0]
        right = sorted_hands[1]
        l_index, r_index = left.points[8], right.points[8]
        l_thumb, r_thumb = left.points[4], right.points[4]

        scale = (self._palm_size(left) + self._palm_size(right)) / 2.0
        if scale <= 0:
            scale = 80.0

        # indici tra loro molto vicini; pollici tra loro abbastanza vicini
        idx_close = self._distance(l_index, r_index) <= 0.45 * scale
        thm_close = self._distance(l_thumb, r_thumb) <= 0.50 * scale

        # indici chiaramente sopra i pollici e ad altezza simile
        indices_above = (l_index[1] < l_thumb[1] - 0.12*scale) and (r_index[1] < r_thumb[1] - 0.12*scale)
        indices_level = abs(l_index[1] - r_index[1]) <= 0.30 * scale

        # per mano: indice-pollice non troppo vicini né troppo lontani (evita pinch)
        d_l = self._distance(l_index, l_thumb)
        d_r = self._distance(r_index, r_thumb)
        min_it = 0.22 * scale
        max_it = 0.75 * scale
        per_hand_ok = (min_it <= d_l <= max_it) and (min_it <= d_r <= max_it)

        if idx_close and thm_close and indices_above and indices_level and per_hand_ok:
            idx_d = self._distance(l_index, r_index)
            thm_d = self._distance(l_thumb, r_thumb)
            closeness = max(0.0, 1.0 - (idx_d + thm_d) / (1.0 * scale))
            return 0.92 + 0.08 * min(1.0, closeness)
        return 0.0

    def _detect_middle_finger(self, sorted_hands: List[HandLandmarks]) -> Tuple[float, int]:
        """
        Rileva il gesto del dito medio: solo il dito medio esteso, altre dita chiuse/piegate.
        MediaPipe landmarks per la mano:
        - 8: index tip, 5: index MCP
        - 12: middle tip, 9: middle MCP  
        - 16: ring tip, 13: ring MCP
        - 20: pinky tip, 17: pinky MCP
        - 4: thumb tip, 3: thumb IP
        - 0: wrist
        """
        if not sorted_hands:
            return 0.0, 0
            
        max_conf = 0.0
        hands_detected = 0
        
        for hand in sorted_hands:
            conf = self._detect_single_middle_finger(hand)
            if conf >= 0.85:
                hands_detected += 1
                max_conf = max(max_conf, conf)
                
        return max_conf, hands_detected
    
    def _detect_single_middle_finger(self, hand: HandLandmarks) -> float:
        """Rileva dito medio su una singola mano."""
        wrist = hand.points[0]
        
        # Landmarks delle dita
        thumb_tip, thumb_ip = hand.points[4], hand.points[3]
        index_tip, index_mcp = hand.points[8], hand.points[5]
        middle_tip, middle_mcp = hand.points[12], hand.points[9]
        ring_tip, ring_mcp = hand.points[16], hand.points[13]
        pinky_tip, pinky_mcp = hand.points[20], hand.points[17]
        
        scale = self._palm_size(hand)
        if scale <= 20:
            return 0.0
            
        # 1. Il dito medio deve essere chiaramente esteso
        middle_dist_from_wrist = self._distance(middle_tip, wrist)
        middle_mcp_dist_from_wrist = self._distance(middle_mcp, wrist)
        middle_extension = middle_dist_from_wrist - middle_mcp_dist_from_wrist
        
        if middle_extension < 0.3 * scale:  # Dito medio non abbastanza esteso
            return 0.0
            
        # 2. Le altre dita devono essere piegate/chiuse
        fingers_data = [
            (index_tip, index_mcp, "index"),
            (ring_tip, ring_mcp, "ring"), 
            (pinky_tip, pinky_mcp, "pinky")
        ]
        
        folded_fingers = 0
        for tip, mcp, name in fingers_data:
            tip_dist = self._distance(tip, wrist)
            mcp_dist = self._distance(mcp, wrist)
            extension = tip_dist - mcp_dist
            
            # Le dita devono essere meno estese del dito medio
            if extension < 0.6 * middle_extension:
                folded_fingers += 1
                
        # 3. Il pollice dovrebbe essere piegato o nascosto
        thumb_dist = self._distance(thumb_tip, wrist)
        thumb_base_dist = self._distance(thumb_ip, wrist)
        thumb_extension = thumb_dist - thumb_base_dist
        
        thumb_folded = thumb_extension < 0.4 * middle_extension
        
        # 4. Calcola confidenza basata su quante dita sono correttamente piegate
        confidence = 0.0
        
        if folded_fingers >= 2:  # Almeno 2 delle 3 dita (index, ring, pinky) piegate
            confidence += 0.6
            
        if folded_fingers == 3:  # Tutte e 3 le dita piegate
            confidence += 0.2
            
        if thumb_folded:  # Pollice piegato
            confidence += 0.2
            
        # 5. Bonus se il dito medio è molto prominente
        if middle_extension > 0.5 * scale:
            confidence += 0.1
            
        return min(1.0, confidence)
