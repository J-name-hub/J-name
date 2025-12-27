'use client';

import { useEffect } from 'react';
import APP_VERSION from '../config/version';

const CacheManager = () => {
  useEffect(() => {
    const checkVersion = async () => {
      try {
        const STORAGE_KEY = 'wedding_app_version';
        const storedVersion = localStorage.getItem(STORAGE_KEY);
        const currentVersion = APP_VERSION.version;
        
        console.log('Stored version:', storedVersion);
        console.log('Current version:', currentVersion);
        console.log('Build time:', APP_VERSION.buildTime);
        
        if (storedVersion !== currentVersion) {
          console.log('🔄 New version detected! Clearing cache...');
          
          const preserveKeys = ['wedding_guest_book', 'wedding_attendance'];
          const dataToPreserve: { [key: string]: string } = {};
          
          preserveKeys.forEach(key => {
            const value = localStorage.getItem(key);
            if (value) dataToPreserve[key] = value;
          });
          
          localStorage.clear();
          
          Object.entries(dataToPreserve).forEach(([key, value]) => {
            localStorage.setItem(key, value);
          });
          
          sessionStorage.clear();
          
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(registrations => {
              registrations.forEach(registration => {
                registration.unregister();
              });
            });
          }
          
          if ('caches' in window) {
            caches.keys().then(names => {
              names.forEach(name => {
                caches.delete(name);
              });
            });
          }
          
          localStorage.setItem(STORAGE_KEY, currentVersion);
          
          setTimeout(() => {
            window.location.reload();
          }, 1000);
          
          return;
        }
        
        if (!storedVersion) {
          localStorage.setItem(STORAGE_KEY, currentVersion);
        }
        
      } catch (error) {
        console.error('Version check failed:', error);
      }
    };
    
    checkVersion();
    
    const interval = setInterval(checkVersion, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  return null;
};

export default CacheManager; 