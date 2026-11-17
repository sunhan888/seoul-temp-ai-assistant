// Vercel 빌드 스크립트
// 정적 사이트(HTML/JS)는 서버의 환경 변수를 직접 읽을 수 없어서,
// 빌드할 때 API_BASE_URL 값을 config.js 파일로 '구워서' dist/ 에 넣습니다.
const fs = require("fs");

const OUT = "dist";
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT);
for (const f of ["index.html", "style.css", "app.js"]) fs.copyFileSync(f, `${OUT}/${f}`);

const url = process.env.API_BASE_URL;
if (!url) console.warn("⚠️ API_BASE_URL 환경 변수가 없습니다. 로컬 주소를 사용합니다.");
fs.writeFileSync(
  `${OUT}/config.js`,
  `window.API_BASE_URL = ${JSON.stringify(url || "http://127.0.0.1:8000")};\n`
);
console.log(`✅ dist/ 생성 완료 (API_BASE_URL=${url || "http://127.0.0.1:8000"})`);
