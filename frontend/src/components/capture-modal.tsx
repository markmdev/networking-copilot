'use client';

import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { X } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';

interface CaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (imageFile: File) => void;
}

export function CaptureModal({ isOpen, onClose, onCapture, isProcessing = false }: CaptureModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const startCamera = useCallback(async () => {
    setIsLoading(true);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'user',
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      });
      
      setStream(mediaStream);
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        
        // Wait for the video to be ready
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch(e => console.error('Play failed:', e));
        };
      }
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Could not access camera. Please check permissions.');
    }
    setIsLoading(false);
  }, []);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => {
        track.stop();
      });
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, [stream]);

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [isOpen, startCamera, stopCamera]);

  // Separate effect to handle setting the video source when both video ref and stream are ready
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  const handleClose = () => {
    stopCamera();
    onClose();
  };

  const handleTakePicture = () => {
    console.log('📸 Take picture button clicked');
    
    if (videoRef.current && canvasRef.current) {
      console.log('📹 Video and canvas elements available');
      
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      console.log('🎨 Canvas dimensions set:', { width: canvas.width, height: canvas.height });

      ctx?.drawImage(video, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(async (blob) => {
        if (blob) {
console.log('📦 Blob created:', { size: blob.size, type: blob.type });
          
          // Convert blob to File with proper metadata
          const timestamp = Date.now();
          const imageFile = new File([blob], `capture-${timestamp}.jpg`, {
            type: 'image/jpeg',
            lastModified: timestamp
          });
          
          console.log('📄 File created:', { 
            name: imageFile.name, 
            type: imageFile.type, 
            size: imageFile.size 
          });
          
          console.log('🚀 Calling onCapture with file...');
          onCapture(imageFile);
        } else {
          console.error('❌ Failed to create blob from canvas');
        }
      }, 'image/jpeg', 0.8);
    } else {
      console.error('❌ Video or canvas element not available', {
        video: !!videoRef.current,
        canvas: !!canvasRef.current
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Capture Contact</h2>
            <Button variant="ghost" size="sm" onClick={handleClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-4">
            <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
              {isLoading ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <p className="text-sm text-gray-500">Loading camera...</p>
                </div>
              ) : stream ? (
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                  style={{ transform: 'scaleX(-1)' }} // Mirror the video like a selfie
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center">
                  <p className="text-sm text-gray-500">No camera stream</p>
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button onClick={handleTakePicture} className="flex-1" disabled={!stream || isLoading || isProcessing}>
                {isProcessing ? 'Processing...' : 'Take Picture'}
              </Button>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Hidden canvas for capturing the image */}
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
