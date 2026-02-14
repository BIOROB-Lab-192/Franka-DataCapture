"""Facial expression recognition functions. Using a pre-trained pytorch model"""

import asyncio
import time

import cv2
import torch
from torch.export import load
from torchvision import transforms


class Expression:
    def __init__(self, model_path, frame_queue, device="cpu"):
        self.name = "expression"
        self.device = device
        self.frame_queue = frame_queue
        self.program = load(model_path)
        self.model = self.program.module().to(self.device)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.preprocess = transforms.Compose(
            [
                # transforms.Resize((100, 100)),
                transforms.ToTensor(),
            ]
        )

    def read_image(self):
        try:
            image = self.frame_queue.get_nowait()
        except asyncio.QueueEmpty:
            # Return None if no new frame is available yet
            return None   
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )

        if len(faces) == 0:
            return None

        x, y, w, h = faces[0]

        image = image[y : y + h, x : x + w]
        image = cv2.resize(image, (100, 100))
        return image

    def load_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_tensor = self.preprocess(image)
        input_batch = input_tensor.unsqueeze(0)
        return input_batch.to(self.device)

    @torch.no_grad()
    def predict(self, image):
        x = self.load_image(image)
        logits = self.model(x)
        probs = torch.softmax(logits, dim=1)
        pred = probs.argmax(dim=1).item()
        return pred, probs.squeeze().cpu()

    def read(self):
        image = self.read_image()

        if image is not None:
            prediction, probs = self.predict(image)
        else:
            # No frame available or no face detected
            prediction = -1

        return {
            "timestamp": time.time(),
            "data": {"happy_index": prediction},
            "source": self.name,
        }
