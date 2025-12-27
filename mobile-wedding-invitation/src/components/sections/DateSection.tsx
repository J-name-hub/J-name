'use client';

import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { weddingConfig } from '../../config/wedding-config';

interface DateSectionProps {
  bgColor?: 'white' | 'beige';
}

const DateSection = ({ bgColor = 'white' }: DateSectionProps) => {
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  });
  
  const [isWeddingPassed, setIsWeddingPassed] = useState(false);
  
  // 달력 생성 로직
  const generateCalendar = () => {
    const { year, month, day } = weddingConfig.date;
    
    // 해당 월의 첫째 날과 마지막 날 계산
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    const startDayOfWeek = firstDay.getDay(); // 0 = 일요일, 1 = 월요일, ...
    const daysInMonth = lastDay.getDate();
    
    const calendarDays = [];
    
    // 첫 주의 빈 칸들 추가
    for (let i = 0; i < startDayOfWeek; i++) {
      calendarDays.push(<div key={`empty-${i}`}></div>);
    }
    
    // 실제 날짜들 추가
    for (let date = 1; date <= daysInMonth; date++) {
      const currentDate = new Date(year, month - 1, date);
      const dayOfWeek = currentDate.getDay();
      const isWeddingDay = date === day;
      
      let weekendType: string | undefined;
      if (dayOfWeek === 0) weekendType = 'sun';
      else if (dayOfWeek === 6) weekendType = 'sat';
      
      if (isWeddingDay) {
        calendarDays.push(
          <WeddingDay key={date}>{date}</WeddingDay>
        );
      } else {
        calendarDays.push(
          <Day key={date} $isWeekend={weekendType}>
            {date}
          </Day>
        );
      }
    }
    
    return calendarDays;
  };
  
  useEffect(() => {
    const calculateTimeLeft = () => {
      const weddingDate = new Date(
        weddingConfig.date.year,
        weddingConfig.date.month - 1,
        weddingConfig.date.day,
        weddingConfig.date.hour,
        weddingConfig.date.minute
      );
      
      const now = new Date();
      const difference = weddingDate.getTime() - now.getTime();
      
      if (difference > 0) {
        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((difference / 1000 / 60) % 60);
        const seconds = Math.floor((difference / 1000) % 60);
        
        setTimeLeft({ days, hours, minutes, seconds });
        setIsWeddingPassed(false);
      } else {
        // 결혼식이 지났음
        setIsWeddingPassed(true);
      }
    };
    
    calculateTimeLeft();
    const timer = setInterval(calculateTimeLeft, 1000);
    
    return () => clearInterval(timer);
  }, []);

  return (
    <DateSectionContainer $bgColor={bgColor}>
      <SectionTitle>일정</SectionTitle>
      
      <CalendarCard>
        <CalendarHeader>
          <span>{weddingConfig.date.year}년 {weddingConfig.date.month}월</span>
          <div>
            <button aria-label="이전 달"><i className="fas fa-chevron-left"></i></button>
            <button aria-label="다음 달"><i className="fas fa-chevron-right"></i></button>
          </div>
        </CalendarHeader>
        
        <CalendarGrid>
          <DayName $isWeekend="sun">일</DayName>
          <DayName>월</DayName>
          <DayName>화</DayName>
          <DayName>수</DayName>
          <DayName>목</DayName>
          <DayName>금</DayName>
          <DayName $isWeekend="sat">토</DayName>
          
          {generateCalendar()}
        </CalendarGrid>
      </CalendarCard>
      
      {!isWeddingPassed && (
        <CountdownContainer>
          <CountdownTitle>결혼까지 남은 시간</CountdownTitle>
          
          <CountdownWrapper>
            <CountdownItem>
              <CountdownValue>{timeLeft.days}</CountdownValue>
              <CountdownLabel>일</CountdownLabel>
            </CountdownItem>
            <VerticalDivider />
            <CountdownItem>
              <CountdownValue>
                {timeLeft.hours < 10 ? `0${timeLeft.hours}` : timeLeft.hours}
              </CountdownValue>
              <CountdownLabel>시간</CountdownLabel>
            </CountdownItem>
            <VerticalDivider />
            <CountdownItem>
              <CountdownValue>
                {timeLeft.minutes < 10 ? `0${timeLeft.minutes}` : timeLeft.minutes}
              </CountdownValue>
              <CountdownLabel>분</CountdownLabel>
            </CountdownItem>
            <VerticalDivider />
            <CountdownItem>
              <CountdownValue>
                {timeLeft.seconds < 10 ? `0${timeLeft.seconds}` : timeLeft.seconds}
              </CountdownValue>
              <CountdownLabel>초</CountdownLabel>
            </CountdownItem>
          </CountdownWrapper>
        </CountdownContainer>
      )}
      
      <WeddingDate>
        {weddingConfig.main.date}
      </WeddingDate>
    </DateSectionContainer>
  );
};

const DateSectionContainer = styled.section<{ $bgColor: 'white' | 'beige' }>`
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

const CalendarCard = styled.div`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  padding: 1.5rem;
  margin-bottom: 2rem;
  max-width: 36rem;
  margin-left: auto;
  margin-right: auto;
`;

const CalendarHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  
  button {
    border: none;
    background: none;
    color: #999;
    cursor: pointer;
    padding: 0.5rem;
    
    &:hover {
      color: #333;
    }
  }
`;

const CalendarGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.5rem;
  text-align: center;
`;

const DayName = styled.div<{ $isWeekend?: string }>`
  color: ${props => 
    props.$isWeekend === 'sun' ? '#e57373' : 
    props.$isWeekend === 'sat' ? '#64b5f6' : 
    'inherit'
  };
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
`;

const Day = styled.div<{ $isWeekend?: string }>`
  color: ${props => 
    props.$isWeekend === 'sun' ? '#e57373' : 
    props.$isWeekend === 'sat' ? '#64b5f6' : 
    'inherit'
  };
  padding: 0.5rem 0;
  font-size: 0.875rem;
`;

const WeddingDay = styled.div`
  background-color: var(--secondary-color);
  color: white;
  border-radius: 50%;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  font-size: 0.875rem;
`;

const CountdownContainer = styled.div`
  margin: 2rem 0;
  width: 100%;
  
  @media (max-width: 600px) {
    overflow-x: none;
  }
`;

const CountdownTitle = styled.h3`
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  font-weight: 500;
`;

const CountdownWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: nowrap;
  min-width: fit-content;
  margin: 0 auto;
  
  @media (max-width: 400px) {
    transform: scale(0.95);
    transform-origin: center center;
  }

  @media (max-width: 370px) {
    transform: scale(0.8);
    transform-origin: center center;
  }

  @media (max-width: 340px) {
    transform: scale(0.65);
    transform-origin: center center;
  }
  
  @media (max-width: 300px) {
    transform: scale(0.5);
    transform-origin: center center;
  }
`;

const CountdownItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 1rem;
  
  @media (max-width: 480px) {
    padding: 0 0.75rem;
  }
`;

const CountdownValue = styled.div`
  font-size: 2rem;
  font-weight: 500;
  color: var(--secondary-color);
  font-family: 'Courier New', monospace;
  min-width: 3rem;
  text-align: center;
  display: inline-block;
  
  @media (max-width: 480px) {
    font-size: 1.85rem;
    min-width: 2.5rem;
  }
`;

const CountdownLabel = styled.div`
  font-size: 0.875rem;
  color: var(--text-medium);
  margin-top: 0.25rem;
  white-space: nowrap;
`;

const VerticalDivider = styled.div`
  height: 4.5rem;
  width: 1px;
  min-width: 1px;
  flex-shrink: 0;
  background-color: var(--secondary-color);
  margin: 0 0.75rem;
  opacity: 0.8;
  
  @media (max-width: 480px) {
    height: 3.75rem;
    margin: 0 0.25rem;
    width: 0.5px;
  }
`;

const WeddingDate = styled.p`
  font-size: 1.25rem;
  margin-top: 2rem;
`;

export default DateSection; 