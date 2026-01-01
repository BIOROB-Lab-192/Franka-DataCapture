"""Facial expression recognition functions. Using a pre-trained pytorch model"""

from torch.export import load
from torchvision import transforms
import torch.no_grad
import time
import asyncio
import cv2

frame_q = asyncio.Queue(maxsize=1)

class Expression:
    def __init__(self, model_path, device='cpu'):
        self.name = "expression"
        self.device = device
        self.program = load(model_path)
        self.model = self.program.module().to(self.device)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.preprocess = transforms.Compose([
            # transforms.Resize((100, 100)),
            transforms.ToTensor(),
        ])

    async def read_image(self):
        image = await frame_q.get()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(40, 40)
                )
        x, y, w, h = faces[0]

        image = image[y:y+h, x:x+w]
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
        try:
            image = await self.read_image()
            prediction = self.predict(image)
        except:
            prediction = -1
        return {
            "timestamp": time.time(),
            "data": {"happy/not": prediction},
            "source": self.name,
        }