const fs = require('fs');
const path = require('path');

// 현재 시간 기반 버전 생성
const now = new Date();
const version = now.getTime().toString();
const buildTime = now.toISOString();
const hash = Math.random().toString(36).substring(2, 15);

// 버전 파일 생성
const versionContent = `// 이 파일은 빌드 시마다 자동으로 업데이트됩니다
// Build Time: ${buildTime}
export const APP_VERSION = {
  version: '${version}',
  buildTime: '${buildTime}',
  hash: '${hash}'
};

export default APP_VERSION;
`;

// 파일 경로 설정
const versionFilePath = path.join(__dirname, '../src/config/version.ts');

// 파일 쓰기
try {
  fs.writeFileSync(versionFilePath, versionContent, 'utf8');
  console.log('✅ Version file updated successfully!');
  console.log(`📦 Version: ${version}`);
  console.log(`🕒 Build Time: ${buildTime}`);
  console.log(`🔑 Hash: ${hash}`);
} catch (error) {
  console.error('❌ Failed to update version file:', error);
  process.exit(1);
} 