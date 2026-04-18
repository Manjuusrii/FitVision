# FitVision — AI-Powered Fitness Trainer

> A real-time virtual personal trainer that uses computer vision and pose estimation to track your workouts, count reps, and correct your form — all through your webcam.

---

## Overview

FitVision is an AI-powered fitness web application that turns your webcam into an intelligent training coach. Using MediaPipe for skeletal pose detection and OpenCV for live video processing, it tracks key body landmarks — shoulders, elbows, hips, knees, wrists — in real time, calculates joint movement angles, counts repetitions, and evaluates whether your form is correct or needs correction.

Beyond real-time analysis, FitVision stores your workout sessions and progress through Firebase, giving you a personal dashboard to track consistency, performance trends, and improvement over time.

---

## Features

- Real-time webcam pose tracking and body landmark detection
- Automatic repetition counting for supported exercises
- AI-based form quality analysis — correct vs. incorrect posture classification
- User authentication — signup, login, and profile management
- Cloud-synced workout history and progress storage
- Personal dashboard with session stats and analytics
- Responsive browser-based interface — no app installation required

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Backend | Python, Flask |
| AI / Computer Vision | OpenCV, MediaPipe, NumPy, TensorFlow |
| Cloud / Auth | Firebase Authentication, Firebase Firestore |

---


## Setup Instructions

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-username/FitVision.git
cd FitVision
```

### Step 2 — Install Python

Recommended version: **Python 3.11.x**

Check your version:

```bash
python --version
```

If Python 3.11 is not installed, download it from [python.org](https://www.python.org/downloads/).

### Step 3 — Create a Virtual Environment

**Windows**
```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

**Mac / Linux**
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install flask
pip install opencv-python
pip install mediapipe==0.10.14
pip install numpy
pip install firebase-admin
pip install pyrebase4
pip install tensorflow
```

---

## Firebase Setup

FitVision uses Firebase for user authentication and cloud storage of workout data.

### Step 1 — Create a Firebase Project

1. Go to [https://console.firebase.google.com](https://console.firebase.google.com)
2. Click **Add Project** → Name it `FitVision` → Click **Create**

### Step 2 — Enable Authentication

1. Go to **Authentication → Get Started**
2. Enable **Email / Password** and click **Save**

### Step 3 — Create a Database

1. Go to **Firestore Database → Create Database**
2. Choose **Start in test mode**
3. Select your nearest region and click **Create**

### Step 4 — Register Your Web App

1. Go to **Project Settings → General → Your Apps → `</>` Web App**
2. Name it `FitVision-Web` and click **Register App**
3. Copy the Firebase config values shown on screen

### Step 5 — Add Your Firebase Config

Open `src/info/firebase_config.json` and replace all placeholder values with your real Firebase project values:

```json
{
  "apiKey": "YOUR_API_KEY",
  "authDomain": "YOUR_PROJECT_ID.firebaseapp.com",
  "databaseURL": "https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com",
  "projectId": "YOUR_PROJECT_ID",
  "storageBucket": "YOUR_PROJECT_ID.appspot.com",
  "messagingSenderId": "YOUR_SENDER_ID",
  "appId": "YOUR_APP_ID"
}
```

**Example (filled in):**
```json
{
  "apiKey": "AIzaSyXXXXXXXXXXXXXXXXXXXXXX",
  "authDomain": "fitvision.firebaseapp.com",
  "databaseURL": "https://fitvision-default-rtdb.firebaseio.com",
  "projectId": "fitvision",
  "storageBucket": "fitvision.appspot.com",
  "messagingSenderId": "123456789012",
  "appId": "1:123456789012:web:abcdef1234567890"
}
```

### Step 6 — (Optional) Firebase Admin for Python Backend

If the backend uses the Firebase Admin SDK:

1. Go to **Project Settings → Service Accounts → Generate New Private Key**
2. Save the downloaded file as `firebase_key.json` inside the `app/` folder
3. Initialize it in Python:

```python
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
```

> `firebase_key.json` is listed in `.gitignore` — never commit it to version control.

---

## Running the Application

```bash
cd app
python routes.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

Allow camera access when prompted — required for pose tracking to work.

---

## Supported Exercises

- Push-ups
- Squats
- Lunges
- Bicep Curls
- Jumping Jacks

---

## How It Works

1. Webcam captures live video frames via OpenCV
2. MediaPipe processes each frame and detects 33 body landmarks
3. Joint angles are calculated from landmark coordinates
4. Repetitions are counted based on movement angle thresholds
5. Form quality is classified as correct or incorrect using ML logic
6. Session data is stored in Firebase and reflected on the dashboard

---

## Troubleshooting

**`mediapipe has no attribute solutions`**
```bash
pip install mediapipe==0.10.14
```
Make sure you are using **Python 3.11**.

---

**Webcam not opening**
- Check that your browser has camera permission enabled
- Make sure no other application is currently using the camera

---

**Firebase errors**
- Verify all values in `src/info/firebase_config.json` match your Firebase project
- Confirm Email/Password Authentication is enabled
- Confirm Firestore Database has been created

---

**Flask not starting**
```bash
pip install flask
```

---

## Security

The following are excluded via `.gitignore` and must never be committed:

```
venv/
__pycache__/
firebase_key.json
.env
```

---

## Author

**ManjuSri**

