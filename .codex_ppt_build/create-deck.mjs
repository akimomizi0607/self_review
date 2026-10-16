import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const SKILL_DIR = "C:/Users/Akito/.codex/plugins/cache/openai-primary-runtime/presentations/26.915.20218/skills/presentations";
const BUILD_DIR = "C:/Users/Akito/ドキュメント/授業/yoshino_senmon/第01回資料集/web_app/.codex_ppt_build";
const WORKSPACE_DIR = "C:/Users/Akito/ドキュメント/授業/yoshino_senmon/第01回資料集/web_app";
const FINAL_PPTX = path.join(WORKSPACE_DIR, "week1", "自分レビュー_第1週発表.pptx");
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
addText(slide1, "自分レビューの要件定義", 60, 36, 1160, 54, 44, COLORS.ink);
addText(slide1, "自分の一日を記録し、星とグラフで振り返る", 60, 100, 1160, 46, 28, COLORS.ink);
addText(slide1, "基本機能", 60, 170, 540, 34, 26, COLORS.accent);
addText(slide1,
  "・一日の出来事を投稿（文章は必須）\n" +
  "・星評価はスレッド設定に応じて入力\n" +
  "・画像は任意：JPG／PNGを最大4枚、各5MBまで\n" +
  "・日別平均を折れ線、投稿数を棒で表示\n" +
  "・全体評価は日別平均の平均。日ごとを同じ重さで集計",
  60, 214, 555, 285, 22, COLORS.ink
);
addText(slide1, "スレッド設定・通知", 670, 170, 550, 34, 26, COLORS.accent);
addText(slide1,
  "・初期スレッド「一日の評価」は削除不可\n" +
  "・新規スレッドは星集計ON／1時間削除OFF\n" +
  "・1時間削除ONなら星集計OFF。本文・画像を削除\n" +
  "・22時にメール通知（初期設定：毎晩）\n" +
  "・PCとアプリサーバー稼働中に送信",
  670, 214, 550, 250, 22, COLORS.ink
);
addText(slide1, "第5週の候補（第4週までの進み具合で再検討）", 60, 535, 1160, 32, 23, COLORS.accent);
addText(slide1, "第一候補：1時間で消えるスレッド　／　候補：画像投稿・22時メール通知", 60, 572, 1160, 35, 21, COLORS.ink);
addText(slide1, "配色：背景 #ECFAFF　文字 #20526B　アクセント #E97832", 60, 646, 1160, 32, 21, COLORS.ink);
slide1.speakerNotes.textFrame.setText("アプリの目的と機能は、学生との相談で決めた内容。");

const slide2 = presentation.slides.add();
slide2.background.fill = COLORS.bg;
addText(slide2, "画面イメージと保存データ", 60, 36, 1160, 54, 44, COLORS.ink);
const imageBytes = new Uint8Array(await fs.readFile(path.join(BUILD_DIR, "self-review-desktop-crop.png")));
slide2.images.add({
  blob: imageBytes,
  contentType: "image/png",
  alt: "自分レビューのPC画面案。全体評価、日別平均の折れ線と投稿件数の棒、スレッド別の今日の投稿が見える。",
  fit: "contain",
  position: { left: 48, top: 112, width: 760, height: 426 },
});
addText(slide2, "操作", 850, 118, 360, 34, 26, COLORS.accent);
addText(slide2,
  "スレッドを選び、文章・必要な星・任意の画像を投稿。\n" +
  "投稿はスレッド内で確認。日付が変わると日別平均を更新。",
  850, 162, 360, 154, 22, COLORS.ink
);
addText(slide2, "保存する情報", 850, 342, 360, 34, 26, COLORS.accent);
addText(slide2,
  "投稿：日付・時刻・スレッド・文章・星・画像名\n" +
  "スレッド：名前・星集計・1時間削除の設定\n" +
  "文章と設定はJSON、画像はファイルとして保存。",
  850, 386, 360, 150, 22, COLORS.ink
);
addText(slide2, "画面の日付・評価・投稿はイメージ用のサンプル", 48, 625, 1160, 34, 22, COLORS.ink);
slide2.speakerNotes.textFrame.setText("数値、日付、投稿文は画面イメージ用のサンプル。画像・メールの仕様は授業の進み具合に合わせて見直す。");

await fs.mkdir(BUILD_DIR, { recursive: true });
for (const [index, slide] of [slide1, slide2].entries()) {
  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(BUILD_DIR, "slide-" + (index + 1) + ".png"), new Uint8Array(await preview.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(BUILD_DIR, "slide-" + (index + 1) + ".layout.json"), await layout.text());
}
const candidatePath = path.join(BUILD_DIR, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const { finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
);
const stagingDir = path.join(BUILD_DIR, "finalizer");
await fs.mkdir(stagingDir, { recursive: true });
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
  receiptPath: path.join(stagingDir, "validation.json"),
});
console.log(JSON.stringify(result, null, 2));
