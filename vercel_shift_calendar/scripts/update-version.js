// scripts/update-version.js
// 빌드 때마다(prebuild) 자동 실행되어 lib/version.ts를 새 버전으로 갱신합니다.
// → 배포할 때 버전을 손으로 바꿀 필요가 없습니다.
const fs = require('fs');
const path = require('path');

const now = new Date();
const version = now.getTime().toString();       // 타임스탬프(ms) 기반 버전
const buildTime = now.toISOString();
const hash = Math.random().toString(36).substring(2, 15);

const versionContent = `// 이 파일은 빌드 시마다 자동으로 업데이트됩니다 (scripts/update-version.js)
// Build Time: ${buildTime}
export const APP_VERSION = {
  version: '${version}',
  buildTime: '${buildTime}',
  hash: '${hash}',
};

export default APP_VERSION;
`;

const versionFilePath = path.join(__dirname, '../lib/version.ts');

try {
  fs.writeFileSync(versionFilePath, versionContent, 'utf8');
  console.log('✅ Version file updated!');
  console.log(`📦 Version: ${version}`);
  console.log(`🕒 Build Time: ${buildTime}`);
  console.log(`🔑 Hash: ${hash}`);
} catch (error) {
  console.error('❌ Failed to update version file:', error);
  process.exit(1);
}
