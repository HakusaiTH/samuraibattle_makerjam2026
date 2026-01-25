import cv2
import mediapipe as mp
import requests
import time

# ================== ตั้งค่า ==================
MIRROR = True

API_URL = "http://localhost:3001/api/attack" 

ZONE_SIZE = 120   # ความหนาขอบ
COOLDOWN = 0.3    # กันซ้อน
# ============================================


mp_pose = mp.solutions.pose
cap = cv2.VideoCapture(0)

last_fire = 0
ready = True   # พร้อมยิงหรือยัง


# =============== ยิง API =================
def fire(direction):
    global last_fire

    now = time.time()

    if now - last_fire < COOLDOWN:
        return False

    try:
        requests.post(
            API_URL,
            json={"direction": direction},
            timeout=2
        )

        print("ยิง:", direction)

        last_fire = now
        return True

    except Exception as e:
        print("ยิงพัง:", e)
        return False
# =========================================


with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as pose:

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        # Mirror
        if MIRROR:
            frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)


        # ============ วาดขอบจอ ============

        # บน
        cv2.rectangle(frame, (0, 0), (w, ZONE_SIZE), (255,255,255), 2)

        # ล่าง
        cv2.rectangle(frame, (0, h-ZONE_SIZE), (w, h), (255,255,255), 2)

        # ซ้าย
        cv2.rectangle(frame, (0, 0), (ZONE_SIZE, h), (255,255,255), 2)

        # ขวา
        cv2.rectangle(frame, (w-ZONE_SIZE, 0), (w, h), (255,255,255), 2)

        # ===================================


        status = "Waiting"


        if result.pose_landmarks:

            lm = result.pose_landmarks.landmark

            # มือขวาตามจอ
            if MIRROR:
                wrist = lm[15]
            else:
                wrist = lm[16]

            x = int(wrist.x * w)
            y = int(wrist.y * h)

            # วาดมือ
            cv2.circle(frame, (x, y), 12, (0,255,0), -1)

            direction = None


            # ============ เช็กโซน ============

            if y < ZONE_SIZE:
                direction = "up"

            elif y > h - ZONE_SIZE:
                direction = "down"

            elif x < ZONE_SIZE:
                direction = "left"

            elif x > w - ZONE_SIZE:
                direction = "right"

            else:
                direction = "center"

            # ===============================


            # ============ ระบบรีเซ็ต ============

            # มือกลับกลาง = พร้อมยิงใหม่
            if direction == "center":
                ready = True
                status = "Ready"

            # ยิงได้เฉพาะตอน ready
            elif ready:

                success = fire(direction)

                if success:
                    ready = False
                    status = f"Fire: {direction}"

            else:
                status = "Reset First"

            # ====================================


        # แสดงสถานะ
        cv2.putText(
            frame,
            f"Status: {status}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2
        )


        cv2.imshow("Pose Reset Controller", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


cap.release()
cv2.destroyAllWindows()
