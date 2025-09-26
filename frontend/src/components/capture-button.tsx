'use client';

import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Camera, Loader2 } from 'lucide-react';
import { Person } from '../types';
import { CaptureModal } from './capture-modal';
import { networkingAPI } from '../lib/api';

interface CaptureButtonProps {
  onCapture: (person: Person) => void;
}

export function CaptureButton({ onCapture }: CaptureButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Test backend connection when component mounts
  useEffect(() => {
    const testBackend = async () => {
      try {
        console.log('🔍 Testing backend connection...');
        await networkingAPI.health();
        console.log('✅ Backend connection successful - ready to capture!');
      } catch (error) {
        console.error('⚠️ Backend connection failed:', error);
        console.log('💡 Make sure to start the backend server:');
        console.log('   cd agents/networking');
        console.log('   source .venv/bin/activate');  
        console.log('   uv run uvicorn networking.api:app --reload');
      }
    };
    
    testBackend();
  }, []);

  const handleImageCapture = async (imageFile: File) => {
    console.log('🎥 Image capture initiated');
    console.log('📁 Image file details:', { 
      name: imageFile.name, 
      type: imageFile.type, 
      size: imageFile.size 
    });
    
    setIsProcessing(true);
    setIsModalOpen(false);
    
    try {
      console.log('🔄 Starting backend API call...');
      
      // Call the backend extract-and-lookup API
      const result = await networkingAPI.extractAndLookup(imageFile);
      
      console.log('✅ Backend API call successful!');
      console.log('📄 Full API Response:', JSON.stringify(result, null, 2));
      
      // Convert the backend response to our frontend Person type
      const newContact: Person = {
        id: `u_${Date.now()}`,
        name: result.person.name || 'Unknown Name',
        role: result.crew_outputs.linkedin_profile_analyzer_task?.current_title || 'Unknown Role',
        company: result.crew_outputs.linkedin_profile_analyzer_task?.current_company || 'Unknown Company',
        email: '', // Not provided in crew outputs, could be extracted from original image data
        phone: '', // Not provided in crew outputs, could be extracted from original image data
        linkedin: result.person.url,
        avatarUrl: result.person.avatar,
        summary: result.crew_outputs.summary_generator_task?.summary || 'No summary available',
        tags: ['Captured', 'AI Analyzed']
      };

      // Add AI analysis data separately to avoid type issues
      (newContact as any).aiAnalysis = {
        highlights: result.crew_outputs.linkedin_profile_analyzer_task?.highlights || [],
        icebreakers: result.crew_outputs.icebreaker_generator_task?.icebreakers || [],
        selectorRationale: result.selector_rationale
      };
      
      console.log('👤 Created new contact:', newContact);
      onCapture(newContact);
      console.log('✨ Profile saved successfully!');
      
    } catch (error) {
      console.error('❌ Failed to process captured image:', error);
      
      // Fallback to mock contact if API fails
      const mockContact: Person = {
        id: `u_${Date.now()}`,
        name: `Captured Contact #${Math.floor(Math.random() * 1000)}`,
        role: 'Processing Failed',
        company: 'Unknown Company',
        email: 'unknown@example.com',
        phone: '+1 (555) 000-0000',
        linkedin: 'linkedin.com/in/unknown',
        summary: 'Failed to process image. Please try again.',
        tags: ['Captured', 'Error']
      };
      
      console.log('🔄 Using fallback mock contact:', mockContact);
      onCapture(mockContact);
      alert(`Failed to process image: ${error}`);
      
    } finally {
      setIsProcessing(false);
      console.log('🏁 Image processing completed');
    }
  };

  return (
    <>
      <Button
        onClick={() => {
          console.log('📹 Capture button clicked - opening modal');
          setIsModalOpen(true);
        }}
        size="sm"
        className="fixed top-4 right-4 z-10"
        disabled={isProcessing}
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <Camera className="w-4 h-4 mr-2" />
            Capture
          </>
        )}
      </Button>
      
      <CaptureModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCapture={handleImageCapture}
      />
    </>
  );
}
