const fs = require("fs");
const path = require("path");

const file = path.join(process.cwd(), "src/config/version.ts");
const now = new Date();
const version = now.toISOString();

fs.writeFileSync(
  file,
  `export const buildVersion = ${JSON.stringify(version)} as const;\n`,
  "utf-8"
);
console.log("Updated build version:", version);
