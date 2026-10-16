import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const SKILL_DIR = "C:/Users/Akito/.codex/plugins/cache/openai-primary-runtime/presentations/26.915.20218/skills/presentations";
const BUILD_DIR = "C:/Users/Akito/ドキュメント/授業/yoshino_senmon/第01回資料集/web_app/.codex_ppt_build";
const WORKSPACE_DIR = "C:/Users/Akito/ドキュメント/授業/yoshino_senmon/第01回資料集/web_app";
const FINAL_PPTX = path.join(WORKSPACE_DIR, "week1", "第1週_日報_まとめ_修正版.pptx");
const COLORS = { bg: "#ECFAFF", ink: "#20526B", accent: "#E97832", white: "#FFFFFF" };
const { resolvePresentationFont } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
);
const family = resolvePresentationFont({ fontFamily: "Meiryo" });
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function addText(slide, text, left, top, width, height, fontSize, color, alignment = "left") {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: family,
    fontSize,
    bold: true,
    color,
    alignment,
    verticalAlignment: "top",
    autoFit: "none",
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

const slide1 = presentation.slides.add();
slide1.background.fill = COLORS.bg;
addText(slide1, "第1週 日報｜作業と自己評価", 58, 34, 1164, 58, 42, COLORS.ink);
addText(slide1, "自分レビュー　｜　2026年9月25日", 60, 102, 1160, 42, 27, COLORS.ink);
addText(slide1, "今日の作業", 60, 184, 520, 36, 27, COLORS.accent);
addText(slide1,
  "・要件定義・基本設計とPC／スマートフォン画面案を整理\n" +
  "・発表用PowerPoint（要件定義＋基本設計の2枚）を作成\n" +
  "・Python、pip、Git、.venv、Flaskを準備\n" +
  "・一時的なFlask確認ページをブラウザーに表示",
  60, 236, 540, 250, 24, COLORS.ink
);
addText(slide1, "本人の自己評価", 665, 184, 540, 36, 27, COLORS.accent);
addText(slide1, "作業進行度　20％", 665, 238, 520, 52, 36, COLORS.ink);
addText(slide1, "理解度　制作物 60％　／　技術 0％", 665, 310, 540, 48, 28, COLORS.ink);
addText(slide1, "分かったこと　設計の進め方", 665, 390, 540, 36, 23, COLORS.ink);
addText(slide1, "まだよく分からないこと　技術面全般", 665, 444, 560, 65, 23, COLORS.ink);
addText(slide1, "環境構築の結果：先生の確認済み", 60, 616, 1160, 34, 22, COLORS.ink);
slide1.speakerNotes.textFrame.setText("進行度・理解度は本人の自己評価。環境構築結果は先生に確認済み。");

const slide2 = presentation.slides.add();
slide2.background.fill = COLORS.bg;
addText(slide2, "環境準備・次回の予定", 58, 34, 1164, 58, 42, COLORS.ink);
addText(slide2, "準備・動作確認", 60, 132, 530, 36, 27, COLORS.accent);
addText(slide2,
  "Python 3.14.7・pip 26.2.1　確認済み\n" +
  "Git 2.54.0　確認済み（第1週はコミットなし）\n" +
  ".venv作成・Flask 3.1.3の読み込み　確認済み\n" +
  "一時的な確認ページ　ブラウザー表示済み。サーバー停止済み。\n" +
  "ChatGPT Plus・Chatタブ　未確認",
  60, 184, 550, 300, 23, COLORS.ink
);
addText(slide2, "次回やること", 680, 132, 540, 36, 27, COLORS.accent);
addText(slide2,
  "1　環境が使える状態か確認する\n" +
  "2　設計に沿って実装を進める大まかな筋道を確認する\n\n" +
  "未確認：ChatGPT Plusの契約状態・Chatタブの利用\n" +
  "Gitリポジトリの初期化・コミットはしていない",
  680, 184, 540, 290, 23, COLORS.ink
);
slide2.speakerNotes.textFrame.setText("未確認の項目は完了とせず、必要なら次回に確認する。");

await fs.mkdir(BUILD_DIR, { recursive: true });
for (const [index, slide] of [slide1, slide2].entries()) {
  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(BUILD_DIR, "diary-slide-" + (index + 1) + ".png"), new Uint8Array(await preview.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(BUILD_DIR, "diary-slide-" + (index + 1) + ".layout.json"), await layout.text());
}
const candidatePath = path.join(BUILD_DIR, "diary-candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const { finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
);
const receiptPath = path.join(BUILD_DIR, "finalizer", "diary-revision-validation.json");
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
const result = await finalizePresentation({
  explicitTotalSlideCount: 2,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [],
  workspaceDir: WORKSPACE_DIR,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: "C:/Users/Akito/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit"],
  fontPolicy: { basis: "user_request", families: ["Meiryo"] },
  verifyArtifactToolImport: true,
  receiptPath,
});
console.log(JSON.stringify(result, null, 2));
