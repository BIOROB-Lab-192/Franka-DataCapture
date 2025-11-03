"""Functions to write the video capture dict, paths will be linked within the csv."""

import cv2
import time
import pathlib
import numpy as np


class VideoWriter:
    def __init__(self, output_dir, identity, width=1920, height=1080, fps=30):
        """Initialize a video writer to save frames to a file.
        
        Args:
            output_dir: Directory to save the video file
            identity: Identifier for the video file
            width: Width of the video frame
            height: Height of the video frame
            fps: Frames per second
        """
        self.output_dir = pathlib.Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.video_path = self.output_dir / f"{identity}.avi"
        self.width = width
        self.height = height
        self.fps = fps
        
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.writer = cv2.VideoWriter(str(self.video_path), self.fourcc, self.fps, (self.width, self.height))
        self.frame_timestamps = []
        
    def write_frame(self, frame, timestamp=None):
        """Write a frame to the video file with timestamp overlay.
        
        Args:
            frame: The frame to write
            timestamp: Optional timestamp to associate with the frame
        
        Returns:
            timestamp: The timestamp associated with the frame
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Add timestamp to the frame
        frame_with_timestamp = frame.copy()
        cv2.putText(
            frame_with_timestamp,
            f"Time: {timestamp:.6f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )
        
        self.writer.write(frame_with_timestamp)
        self.frame_timestamps.append(timestamp)
        
        return timestamp
    
    def get_video_info(self):
        """Get information about the video file.
        
        Returns:
            dict: Information about the video file
        """
        return {
            "path": str(self.video_path),
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frame_count": len(self.frame_timestamps),
            "duration": self.frame_timestamps[-1] - self.frame_timestamps[0] if self.frame_timestamps else 0
        }
    
    def release(self):
        """Release the video writer."""
        self.writer.release()
        
    def __del__(self):
        """Ensure the video writer is released when the object is deleted."""
        if hasattr(self, 'writer'):
            self.writer.release()