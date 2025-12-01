"""Facial expression recognition functions. Using a pre-trained pytorch model"""

from torch.export import load
from torchvision import transforms
import torch.no_grad
import random
import time


class Expression:
    def __init__(self, model_path, device='cpu'):
        self.name = "expression"
        self.device = device
        self.program = load(model_path)
        self.model = self.program.module().to(self.device)
        
        self.preprocess = transforms.Compose([
            transforms.Resize(100),
            # transforms.CenterCrop(224),
            transforms.ToTensor(),
        ])

    def load_image(self, image):
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
            prediction = self.predict(image)
        except:
            prediction = -1
        return {
            "timestamp": time.time(),
            "data": {"happy/not": prediction},
            "source": self.name,
        }