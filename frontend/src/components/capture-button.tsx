'use client';

import { useState } from 'react';
import { Button } from './ui/button';
import { Camera } from 'lucide-react';
import { PersonDetail } from '../types';
import { CaptureModal } from './capture-modal';
import { uploadExtractAndLookup } from '../lib/api';

interface CaptureButtonProps {
  onCapture: (record: PersonDetail) => void;
}

export function CaptureButton({ onCapture }: CaptureButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleImageCapture = async (imageBlob: Blob) => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      const record = await uploadExtractAndLookup(imageBlob);
      onCapture(record);
      setIsModalOpen(false);
    } catch (error) {
      console.error('Failed to process image', error);
      alert('Failed to process the image. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <>
      <Button
        onClick={() => setIsModalOpen(true)}
        size="sm"
        className="fixed top-4 right-4 z-10"
        disabled={isProcessing}
      >
        <Camera className="w-4 h-4 mr-2" />
        {isProcessing ? 'Processing...' : 'Capture'}
      </Button>

      <CaptureModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCapture={handleImageCapture}
        isProcessing={isProcessing}
      />
    </>
  );
}
