import cv2 as cv
import mediapipe as mp
import numpy as np
import json
import os

# Initialize Mediapipe Pose
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Load exercise joint config from data_info.json
_config_path = os.path.join(os.path.dirname(__file__), 'static', 'data_info.json')
with open(_config_path, 'r') as f:
    _data_info = json.load(f)

_joints_map = _data_info['joints']       # e.g. {"lElbow": [11,13,15], ...}
_exercises  = _data_info['exercises']    # e.g. {"pushup": {"joints": [...], "frames": 200}}
_decimals   = _data_info['decimals']     # 3

# This holds the most recently computed prediction score (0-100 float or None)
_latest_prediction = None

# This accumulates raw angle data during an active rep
_rep_angles = {}   # { joint_name: [angle, angle, ...] }


def find_angle(a, b, c):
    """Return the angle at point b, formed by a-b-c, in degrees."""
    a = (a.x, a.y)
    b = (b.x, b.y)
    c = (c.x, c.y)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


def _interpolate_to_fixed_frames(angle_list, target_frames):
    """
    Linearly interpolate a variable-length list of angles down to
    exactly `target_frames` values, matching the data_creation.py logic.
    """
    cur_size = len(angle_list)
    if cur_size == 0:
        return [0.0] * target_frames
    if cur_size == 1:
        return [angle_list[0]] * target_frames

    interval = (cur_size - 1) / target_frames
    result = []
    for n in range(target_frames):
        ei = interval * n
        v1 = angle_list[int(ei)]
        v2 = angle_list[min(int(ei) + 1, cur_size - 1)]
        est = (v2 - v1) * (ei % 1) + v1
        result.append(round(est, _decimals))
    return result


def _score_rep(exercise):
    """
    Given accumulated _rep_angles for `exercise`, normalize to fixed frames
    and run through the TensorFlow model.  Returns a score 0-100 (float),
    or None if the model file is not found.
    """
    global _rep_angles

    if exercise not in _exercises:
        return None

    ex_cfg = _exercises[exercise]
    joint_names = ex_cfg['joints']
    target_frames = ex_cfg['frames']

    # Build the flat feature vector  [joint0_f0, joint0_f1, ..., joint1_f0, ...]
    feature_vector = []
    for jname in joint_names:
        raw = _rep_angles.get(jname, [])
        normalized = _interpolate_to_fixed_frames(raw, target_frames)
        feature_vector.extend(normalized)

    # Attempt to load the model and predict
    model_path = os.path.join(os.path.dirname(__file__), 'models', f'{exercise}.h5')
    if not os.path.exists(model_path):
        # No model trained yet – return a placeholder score of 0
        print(f'[webcam] WARNING: model not found at {model_path}. Returning score 0.')
        return 0.0

    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(model_path, compile=False)
        x = np.array(feature_vector, dtype=np.float32).reshape(1, -1)
        prediction = float(model.predict(x, verbose=0)[0][0])
        # sigmoid output is 0-1, convert to 0-100 percentage
        score = round(prediction * 100, 1)
        return score
    except Exception as e:
        print(f'[webcam] Model prediction error: {e}')
        return None


def generate_frames(app_info):
    """
    Flask MJPEG generator.  Yields JPEG bytes forever while the camera is open.

    app_info keys (set by routes.py via POST /video):
        'workout'  : bool  – True while a rep is being recorded
        'exercise' : str   – exercise name, e.g. 'pushup'
    """
    global _latest_prediction, _rep_angles

    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print('[webcam] ERROR: Could not open camera.')
        return

    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    was_recording = False   # tracks transition: recording → not recording

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print('[webcam] ERROR: Could not read frame.')
            break

        # ── Pose detection ──────────────────────────────────────────────
        image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv.cvtColor(image, cv.COLOR_RGB2BGR)

        # ── Draw skeleton if landmarks found ───────────────────────────
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )

            landmarks = results.pose_landmarks.landmark
            currently_recording = app_info.get('workout', False)
            exercise = app_info.get('exercise', '')

            # ── If a rep just ended, score it ──────────────────────────
            if was_recording and not currently_recording:
                _latest_prediction = _score_rep(exercise)
                _rep_angles = {}   # clear for next rep
                print(f'[webcam] Rep ended. Score: {_latest_prediction}')

            # ── If recording, accumulate joint angles ──────────────────
            if currently_recording and exercise in _exercises:
                ex_cfg = _exercises[exercise]
                for jname in ex_cfg['joints']:
                    indices = _joints_map[jname]       # e.g. [11, 13, 15]
                    a = landmarks[indices[0]]
                    b = landmarks[indices[1]]
                    c = landmarks[indices[2]]
                    angle = find_angle(a, b, c)

                    if jname not in _rep_angles:
                        _rep_angles[jname] = []
                    _rep_angles[jname].append(angle)

            was_recording = currently_recording

            # ── Overlay status text on the frame ───────────────────────
            status = 'RECORDING' if app_info.get('workout', False) else 'READY'
            color  = (0, 0, 255) if status == 'RECORDING' else (0, 200, 0)
            cv.putText(image, status, (20, 40),
                       cv.FONT_HERSHEY_SIMPLEX, 1.2, color, 2, cv.LINE_AA)

            if _latest_prediction is not None:
                cv.putText(image, f'Last Score: {_latest_prediction}%', (20, 80),
                           cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv.LINE_AA)

        # ── Encode frame as JPEG and yield ─────────────────────────────
        success, buffer = cv.imencode('.jpg', image)
        if not success:
            continue

        frame_bytes = buffer.tobytes()
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame_bytes +
            b'\r\n'
        )

    cap.release()


def send_prediction():
    """
    Called by routes.py GET /get-model-response.
    Returns the latest prediction score (float 0-100) or None.
    """
    return _latest_prediction