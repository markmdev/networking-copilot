'use client';

import { useState } from 'react';
import { Button } from './ui/button';
import { Camera } from 'lucide-react';
import { Person } from '../types';
import { CaptureModal } from './capture-modal';

interface CaptureButtonProps {
  onCapture: (person: Person) => void;
}

export function CaptureButton({ onCapture }: CaptureButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleImageCapture = (imageBlob: Blob) => {
    // Create a mock person for now (later this would process the image)
    const newContact: Person = {
      id: `u_${Date.now()}`,
      name: `New Contact #${Math.floor(Math.random() * 1000)}`,
      role: 'Unknown Role',
      company: 'Unknown Company',
      email: 'unknown@example.com',
      phone: '+1 (555) 000-0000',
      linkedin: 'linkedin.com/in/unknown',
      summary: 'Captured from image (processing pending).',
      tags: ['New', 'Captured']
    };
    
    onCapture(newContact);
  };

  return (
    <>
      <Button
        onClick={() => setIsModalOpen(true)}
        size="sm"
        className="fixed top-4 right-4 z-10"
      >
        <Camera className="w-4 h-4 mr-2" />
        Capture
      </Button>
      
      <CaptureModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCapture={handleImageCapture}
      />
    </>
  );
}
