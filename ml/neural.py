"""
neural.py
---------
STEP 2 of the ML pipeline (run this OFFLINE after data_creation.py).

What it does:
  1. Downloads all processed .txt files from Firebase Storage/txt-files/{exercise}/
  2. Assembles them into a local .csv training file
  3. Trains a TensorFlow neural network (binary classification: good form vs bad)
  4. Saves the trained model to  ../app/models/{exercise}.h5

Run from inside  ml/  directory:
    python neural.py

Requirements:
    pip install tensorflow pandas numpy scikit-learn pyrebase4
"""

import pandas as pd
import numpy as np
import csv
import pyrebase
import json
import os
import tensorflow as tf
from copy import deepcopy
from sklearn.model_selection import train_test_split


# ── Custom activation (converts degree angles to sine values) ─────────────────

def sin_activation(x):
    return tf.math.sin(x * (np.pi / 180.0))


# ── Config ────────────────────────────────────────────────────────────────────

EPOCHS = 500

_config_path = os.path.join(os.path.dirname(__file__), 'src', 'info', 'data_creation_options.json')
with open(_config_path, 'r') as f:
    d = json.load(f)

exerciseNames = list(d['exercises'].keys())
exercises     = d['exercises']
metadata_cfg  = d['metadata']   # renamed to avoid clash with local var 'metadata'

# ── Firebase init ─────────────────────────────────────────────────────────────

_fb_config_path = os.path.join(os.path.dirname(__file__), 'src', 'info', 'firebase_config.json')
with open(_fb_config_path, 'r') as fbc:
    firebaseConfig = json.load(fbc)

firebase_app = pyrebase.initialize_app(firebaseConfig)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Neural network trainer.  Available exercises:", exerciseNames)
    exercise = ""
    while exercise not in exerciseNames:
        exercise = input("Enter exercise name: ").strip()

    storage = firebase_app.storage()
    data    = storage.bucket.list_blobs(prefix=f"txt-files/{exercise}")

    # Temp storage directory
    temp_dir = os.path.join(os.path.dirname(__file__), 'src', 'temp-storage')
    os.makedirs(temp_dir, exist_ok=True)

    csv_path = os.path.join(temp_dir, f'{exercise}.csv')

    # ── Build CSV header ──────────────────────────────────────────────
    header     = deepcopy(metadata_cfg['x'])   # ['gender','height','reps','weight']
    x_nodes    = exercises[exercise]['frames'] * len(exercises[exercise]['joints'])
    input_nodes = len(header) + x_nodes        # metadata cols + angle cols

    for i in range(x_nodes):
        header.append(str(i))
    header.append(metadata_cfg['y'])           # 'goodForm' at the end

    print('Writing CSV header...')
    with open(csv_path, 'w', newline='') as c:
        csv.writer(c).writerow(header)

    # ── Download each processed .txt and append a row to the CSV ──────
    row_count = 0
    for file in data:
        if file.name == f"txt-files/{exercise}/":
            continue

        f_name    = file.name.split('/')[-1]
        txt_path  = os.path.join(temp_dir, f_name + '.txt')

        print(f'  Downloading: {f_name}')
        storage = firebase_app.storage()    # re-init each time (pyrebase workaround)
        storage.download(file.name, os.path.abspath(txt_path))

        with open(txt_path, 'r') as f:
            keys      = f.readline().strip().split(',')
            vals      = f.readline().strip().split(',')
            angle_str = f.readline().strip()

        # Build one CSV row: [metadata values] + [angle values] + [goodForm]
        csv_line = []
        for x in metadata_cfg['x']:
            ix = keys.index(str(x))
            csv_line.append(vals[ix])

        csv_line += angle_str.split(',')
        csv_line.append(vals[keys.index(metadata_cfg['y'])])

        with open(csv_path, 'a', newline='') as c:
            csv.writer(c).writerow(csv_line)

        os.remove(txt_path)
        row_count += 1

    print(f'\nCSV built with {row_count} training samples.')

    if row_count == 0:
        print('ERROR: No training data found. Upload videos first via data_creation.py.')
        return

    # ── Ask before training ───────────────────────────────────────────
    while True:
        answer = input('Start ML training? (yes/no): ').strip().lower()
        if answer == 'yes':
            break
        if answer == 'no':
            print('Training cancelled.')
            return

    # ── Load CSV ──────────────────────────────────────────────────────
    ds  = pd.read_csv(csv_path)
    dsx = ds.iloc[:, :-1].values.astype(np.float32)
    dsy = ds.iloc[:,  -1].values.astype(np.float32)

    X_train, X_test, Y_train, Y_test = train_test_split(
        dsx, dsy, test_size=0.2, random_state=42
    )

    X_train = tf.constant(X_train, dtype=tf.float16)
    Y_train = tf.constant(Y_train, dtype=tf.float16)
    X_test  = tf.constant(X_test,  dtype=tf.float16)
    Y_test  = tf.constant(Y_test,  dtype=tf.float16)

    # ── Build model ───────────────────────────────────────────────────
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(25, input_dim=input_nodes, activation=sin_activation),
        tf.keras.layers.Dense(25, activation=sin_activation),
        tf.keras.layers.Dense(25, activation=sin_activation),
        tf.keras.layers.Dense(25, activation=sin_activation),
        tf.keras.layers.Dense(1,  activation='sigmoid'),
    ])

    model.compile(
        loss='mean_squared_error',
        optimizer='adam',
        metrics=['mean_squared_error']
    )

    model.summary()

    # ── Train ─────────────────────────────────────────────────────────
    model.fit(X_train, Y_train, epochs=EPOCHS, verbose=1)

    test_loss = model.evaluate(X_test, Y_test, verbose=0)
    print(f'\nTest Mean Squared Error: {test_loss[1]:.4f}')

    # ── Save model ────────────────────────────────────────────────────
    models_dir  = os.path.join(os.path.dirname(__file__), '..', 'app', 'models')
    os.makedirs(models_dir, exist_ok=True)
    model_path  = os.path.join(models_dir, f'{exercise}.h5')

    model.save(model_path)
    print(f'\nModel saved to: {model_path}')


if __name__ == '__main__':
    main()