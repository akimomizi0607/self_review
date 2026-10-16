const sharp = require("C:/Users/Akito/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp");
(async () => {
  const input = "C:/Users/Akito/ドキュメント/授業/yoshino_senmon/第01回資料集/web_app/.codex_ppt_build/self-review-desktop.png";
  const output = "C:/Users/Akito/ドキュメント/授業/yoshino_senmon/第01回資料集/web_app/.codex_ppt_build/self-review-desktop-crop.png";
  await sharp(input).extract({ left: 130, top: 10, width: 1195, height: 670 }).png().toFile(output);
  console.log(await sharp(output).metadata());
})().catch(error => { console.error(error); process.exit(1); });
