# -*- coding: utf-8 -*-
"""Untitled5.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1x8dgdmVrRxewF6y2zCS8CxlrNzZSLj9a
"""

import os
import pandas as pd
from keras.preprocessing.image import ImageDataGenerator
from keras.applications import MobileNetV2
from keras.layers import GlobalAveragePooling2D, Dense
from keras.models import Model
from keras.optimizers import Adam
import optuna

# Set your parent directories
animal_directory = '/kaggle/input/all-images-for-model/All Images Enhanced/All Images Enhanced'
no_animal_directory = '/kaggle/input/no-animal-images/No animals enchanced/No animals enchanced'

# Create a DataFrame with file paths and labels for "Animal" class
animal_files = [os.path.join(animal_directory, file) for file in os.listdir(animal_directory) if file.endswith(('.jpg', '.jpeg', '.png'))]
animal_labels = [1] * len(animal_files)  # All images contain animals

# Create a DataFrame with file paths and labels for "No Animal" class
no_animal_files = [os.path.join(no_animal_directory, file) for file in os.listdir(no_animal_directory) if file.endswith(('.jpg', '.jpeg', '.png'))]
no_animal_labels = [0] * len(no_animal_files)  # All images are of "No Animal" class

# Combine the two DataFrames
df_animal = pd.DataFrame({'file_path': animal_files, 'label': animal_labels})
df_no_animal = pd.DataFrame({'file_path': no_animal_files, 'label': no_animal_labels})
df = pd.concat([df_animal, df_no_animal], ignore_index=True)
# Convert numerical labels to strings
df['label'] = df['label'].astype(str)
# Define the Optuna objective function
def objective(trial):
    # Create the generator with updated hyperparameters
    datagen = ImageDataGenerator(
        rescale=1./255,
        shear_range=trial.suggest_float('shear_range', 0.0, 0.5),
        zoom_range=trial.suggest_float('zoom_range', 0.0, 0.5),
        horizontal_flip=trial.suggest_categorical('horizontal_flip', [True, False]),
        validation_split=0.2
    )

    generator = datagen.flow_from_dataframe(
        df,
        x_col='file_path',
        y_col='label',
        target_size=(224,224),
        batch_size=16,
        class_mode='binary',
        subset='training'
    )

    # Load pre-trained MobileNetV2 model without the top (fully connected) layers
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

    # Freeze the convolutional layers
    for layer in base_model.layers:
        layer.trainable = False

    # Add a global average pooling layer
    x = GlobalAveragePooling2D()(base_model.output)

    # Add a dense layer for binary classification (sigmoid activation)
    prediction = Dense(1, activation='sigmoid')(x)

    # Create the model
    model = Model(inputs=base_model.input, outputs=prediction)

    # Compile the model with updated hyperparameters
    model.compile(
        optimizer=Adam(learning_rate=trial.suggest_float('learning_rate', 1e-5, 1e-2)),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    # Train the model
    model.fit(
        generator,
        steps_per_epoch=len(generator),
        epochs=5
    )

    # Evaluate the model
    evaluation = model.evaluate(generator)
    return evaluation[0]  # Return validation loss as the objective

# Create the Optuna study
study = optuna.create_study(direction='minimize')

# Optimize the objective function
study.optimize(objective, n_trials=10)

# Get the best hyperparameters
best_params = study.best_params

# Print the best hyperparameters
print("Best Hyperparameters:", best_params)

# Now, after the optimization loop finishes, you can evaluate the best model obtained
if best_model is not None:
    evaluation = best_model.evaluate(generator)
    print(f"Best Model Validation Loss: {evaluation[0]}")
    print(f"Best Model Validation Accuracy: {evaluation[1]}")

    # Save the best model
    best_model.save("Best_MobileNetV2_model.h5")
else:
    print("No best model found.")