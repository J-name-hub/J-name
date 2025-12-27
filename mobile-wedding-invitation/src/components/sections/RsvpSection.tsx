'use client';

import React, { useState } from 'react';
import styled from 'styled-components';
import { weddingConfig } from '../../config/wedding-config';

interface RsvpSectionProps {
  bgColor?: 'white' | 'beige';
}

const RsvpSection = ({ bgColor = 'white' }: RsvpSectionProps) => {
  const [formData, setFormData] = useState({
    name: '',
    isAttending: null as boolean | null,
    guestCount: 1,
    side: '' as 'BRIDE' | 'GROOM' | '',
    hasMeal: null as boolean | null,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  // 식사 여부 옵션 표시 설정
  const showMealOption = weddingConfig.rsvp?.showMealOption ?? true;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleAttendingChange = (value: boolean) => {
    setFormData({
      ...formData,
      isAttending: value,
      guestCount: value ? 1 : 0,
      // 참석하지 않으면 식사 여부도 null로 설정
      hasMeal: value ? formData.hasMeal : null,
    });
  };

  const handleSideChange = (side: 'BRIDE' | 'GROOM') => {
    setFormData({
      ...formData,
      side,
    });
  };

  const handleMealChange = (value: boolean) => {
    setFormData({
      ...formData,
      hasMeal: value,
    });
  };

  const handleGuestCountChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData({
      ...formData,
      guestCount: parseInt(e.target.value, 10),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name || formData.isAttending === null || !formData.side) {
      setSubmitStatus({
        success: false,
        message: '이름, 참석 여부, 신부/신랑측 여부를 모두 입력해주세요.',
      });
      return;
    }
    
    if (showMealOption && formData.isAttending && formData.hasMeal === null) {
      setSubmitStatus({
        success: false,
        message: '식사 여부를 선택해주세요.',
      });
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // 현재 시간을 직접 한국 시간으로 생성
      const now = new Date();
      
      // Slack 웹훅으로 메시지 전송
      const response = await fetch('/api/rsvp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          side: formData.side === 'BRIDE' ? '신부측' : '신랑측',
          isAttending: formData.isAttending,
          guestCount: formData.isAttending ? formData.guestCount : 0,
          hasMeal: formData.isAttending ? formData.hasMeal : false,
          timestamp: now.toISOString(),
        }),
      });
      
      if (response.ok) {
        setSubmitStatus({
          success: true,
          message: '참석 여부가 성공적으로 전송되었습니다. 감사합니다.',
        });
        setFormData({
          name: '',
          isAttending: null,
          guestCount: 1,
          side: '',
          hasMeal: null,
        });
      } else {
        throw new Error('서버 응답 오류');
      }
    } catch (error) {
      console.error('RSVP 제출 오류:', error);
      setSubmitStatus({
        success: false,
        message: '참석 여부 전송 중 오류가 발생했습니다. 다시 시도해 주세요.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <RsvpSectionContainer $bgColor={bgColor}>
      <SectionTitle>참석 여부 회신</SectionTitle>
      
      <RsvpDescription>
        소중한 날에 함께해 주실 수 있는지 알려주세요.<br />
        정성을 다해 준비할 수 있도록<br />
        참석 여부를 알려주시면 진심으로 감사하겠습니다.
      </RsvpDescription>
      
      {submitStatus && (
        <StatusMessage $success={submitStatus.success.toString()}>
          {submitStatus.message}
        </StatusMessage>
      )}
      
      <RsvpForm onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="name">이름</Label>
          <Input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="이름을 입력해 주세요"
            required
          />
        </FormGroup>
        
        <FormRow>
          <FormColumn>
            <Label as="p">신랑/신부측</Label>
            <AttendanceButtons>
              <AttendanceButton 
                type="button"
                $selected={formData.side === 'GROOM'}
                onClick={() => handleSideChange('GROOM')}
              >
                신랑측
              </AttendanceButton>
              <AttendanceButton 
                type="button"
                $selected={formData.side === 'BRIDE'}
                onClick={() => handleSideChange('BRIDE')}
              >
                신부측
              </AttendanceButton>
            </AttendanceButtons>
          </FormColumn>

          <FormColumn>
            <Label as="p">참석 여부</Label>
            <AttendanceButtons>
              <AttendanceButton 
                type="button"
                $selected={formData.isAttending === true}
                onClick={() => handleAttendingChange(true)}
              >
                참석
              </AttendanceButton>
              <AttendanceButton 
                type="button"
                $selected={formData.isAttending === false}
                onClick={() => handleAttendingChange(false)}
              >
                불참
              </AttendanceButton>
            </AttendanceButtons>
          </FormColumn>
        </FormRow>
        
        {formData.isAttending && (
          <FormRow>
            <FormColumn>
              <Label htmlFor="guestCount">참석 인원</Label>
              <Select
                id="guestCount"
                name="guestCount"
                value={formData.guestCount}
                onChange={handleGuestCountChange}
              >
                {[1, 2, 3, 4, 5].map((num) => (
                  <option key={num} value={num}>
                    {num}명
                  </option>
                ))}
              </Select>
            </FormColumn>
            
            {showMealOption && (
              <FormColumn>
                <Label as="p">식사 여부</Label>
                <AttendanceButtons>
                  <AttendanceButton 
                    type="button"
                    $selected={formData.hasMeal === true}
                    onClick={() => handleMealChange(true)}
                  >
                    식사 함
                  </AttendanceButton>
                  <AttendanceButton 
                    type="button"
                    $selected={formData.hasMeal === false}
                    onClick={() => handleMealChange(false)}
                  >
                    식사 안 함
                  </AttendanceButton>
                </AttendanceButtons>
              </FormColumn>
            )}
          </FormRow>
        )}
        
        <SubmitButton type="submit" disabled={isSubmitting}>
          {isSubmitting ? '전송 중...' : '회신하기'}
        </SubmitButton>
      </RsvpForm>
    </RsvpSectionContainer>
  );
};

const RsvpSectionContainer = styled.section<{ $bgColor: 'white' | 'beige' }>`
  padding: 4rem 1.5rem;
  text-align: center;
  background-color: ${props => props.$bgColor === 'beige' ? '#F8F6F2' : 'white'};
`;

const SectionTitle = styled.h2`
  position: relative;
  display: inline-block;
  margin-bottom: 2rem;
  font-weight: 500;
  font-size: 1.5rem;
  
  &::after {
    content: '';
    position: absolute;
    bottom: -16px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--secondary-color);
  }
`;

const RsvpDescription = styled.p`
  margin-bottom: 2rem;
  font-size: 0.9rem;
  color: var(--text-medium);
  line-height: 1.6;
`;

const StatusMessage = styled.div<{ $success: string }>`
  padding: 0.75rem;
  margin-bottom: 1.5rem;
  border-radius: 4px;
  text-align: center;
  font-size: 0.9rem;
  background-color: ${props => props.$success === 'true' ? '#e7f3eb' : '#fbedec'};
  color: ${props => props.$success === 'true' ? '#2e7d32' : '#c62828'};
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
`;

const RsvpForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 36rem;
  margin: 0 auto;
  text-align: left;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const FormRow = styled.div`
  display: flex;
  flex-direction: row;
  gap: 1rem;
  
  @media (max-width: 576px) {
    flex-direction: column;
  }
`;

const FormColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
`;

const Label = styled.label`
  font-size: 0.9rem;
  color: var(--text-dark);
`;

const Input = styled.input`
  padding: 0.75rem;
  border: none;
  border-bottom: 1px solid var(--secondary-color);
  font-size: 1rem;
  background-color: transparent;
  
  &:focus {
    outline: none;
    border-bottom: 1px solid var(--text-dark);
  }
`;

const AttendanceButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const AttendanceButton = styled.button<{ $selected?: boolean }>`
  flex: 1;
  padding: 0.75rem;
  border: 1px solid ${props => props.$selected ? 'var(--secondary-color)' : '#ccc'};
  border-radius: 4px;
  background-color: ${props => props.$selected ? 'var(--secondary-color)' : 'transparent'};
  color: ${props => props.$selected ? 'white' : 'var(--text-medium)'};
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  
  &:hover {
    border-color: var(--secondary-color);
  }
  
  &:after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 5px;
    height: 5px;
    background: rgba(255, 255, 255, 0.5);
    opacity: 0;
    border-radius: 100%;
    transform: scale(1, 1) translate(-50%);
    transform-origin: 50% 50%;
  }
  
  &:active:after {
    animation: ripple 0.6s ease-out;
  }
  
  @keyframes ripple {
    0% {
      transform: scale(0, 0);
      opacity: 0.5;
    }
    20% {
      transform: scale(25, 25);
      opacity: 0.3;
    }
    100% {
      opacity: 0;
      transform: scale(40, 40);
    }
  }
`;

const Select = styled.select`
  padding: 0.75rem;
  border: none;
  border-bottom: 1px solid var(--secondary-color);
  font-size: 1rem;
  background-color: transparent;
  
  &:focus {
    outline: none;
    border-bottom: 1px solid var(--text-dark);
  }
`;

const Textarea = styled.textarea`
  padding: 0.75rem;
  border: 1px solid var(--secondary-color);
  border-radius: 4px;
  font-size: 1rem;
  resize: vertical;
  
  &:focus {
    outline: none;
    border-color: var(--text-dark);
  }
`;

const SubmitButton = styled.button`
  padding: 0.75rem;
  background-color: var(--secondary-color);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  
  &:hover {
    background-color: #c4a986;
    box-shadow: 0 2px 5px rgba(0,0,0,0.15);
  }
  
  &:active {
    transform: translateY(1px);
  }
  
  &:after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 5px;
    height: 5px;
    background: rgba(255, 255, 255, 0.5);
    opacity: 0;
    border-radius: 100%;
    transform: scale(1, 1) translate(-50%);
    transform-origin: 50% 50%;
  }
  
  &:active:after {
    animation: ripple 0.6s ease-out;
  }
  
  &:disabled {
    background-color: #ccc;
    cursor: not-allowed;
    box-shadow: none;
  }
`;

export default RsvpSection; 