import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { weddingConfig } from '../../../src/config/wedding-config';

export async function GET() {
  try {
    // 갤러리 폴더 경로
    const galleryDir = path.join(process.cwd(), 'public/images/gallery');
    
    // 폴더 내 파일 목록 읽기
    const files = fs.readdirSync(galleryDir);
    
    // 이미지 파일 필터링
    const imageFiles = files
      .filter(file => {
        const ext = path.extname(file).toLowerCase();
        return ['.jpg', '.jpeg', '.png', '.gif', '.webp'].includes(ext);
      });
    
    // config 파일에 설정된 순서로 이미지 정렬
    const configImages = weddingConfig.gallery.images;
    const orderedImages: string[] = [];
    
    // config에 설정된 순서대로 존재하는 이미지만 추가
    for (const configImagePath of configImages) {
      const filename = path.basename(configImagePath);
      if (imageFiles.includes(filename)) {
        orderedImages.push(configImagePath);
      }
    }
    
    // config에 없지만 폴더에 존재하는 이미지들을 마지막에 추가 (파일명 순으로 정렬)
    const remainingFiles = imageFiles
      .filter(file => !configImages.some((configPath: string) => path.basename(configPath) === file))
      .sort((a, b) => a.localeCompare(b))
      .map(file => `/images/gallery/${file}`);
    
    const finalImages = [...orderedImages, ...remainingFiles];
    
    return NextResponse.json({ images: finalImages });
  } catch (error) {
    console.error('갤러리 이미지 로드 오류:', error);
    return NextResponse.json(
      { 
        error: '갤러리 이미지를 불러오는 중 오류가 발생했습니다.',
        images: weddingConfig.gallery.images // 에러 시 config 설정 반환
      }, 
      { status: 500 }
    );
  }
} 