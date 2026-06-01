// DynamicConceptMap: 思维导图 / 概念关系图 (套路 #11, X.4 升级版)
//
// 用纯 SVG + div 渲染 (React Flow 在 Remotion SSR 下 fitView 不工作)
// X.4 v4 升级:
//   - 节点分 3 类: root (主题) / main (主分支) / leaf (终点), 颜色 + 字号 + 光晕分级
//   - 入场用 spring 物理 (Remotion 原生 spring)
//   - 边带显眼箭头 + 加粗
//   - 背景微妙径向光让主题节点高亮
//   - 当前最新出现的节点有额外 ring 强调

import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { PALETTES, type Palette } from "../theme";
import {
  FONT_STACK, FONT_WEIGHT,
  LETTER_SPACING, LINE_HEIGHT, SIZE, TYPE_RATIO,
  MOTION_DURATION,
} from "../tokens";

type NodeKind = "root" | "main" | "leaf";

type ConceptNode = {
  id: string;
  label: string;
  /** 屏幕相对坐标 0-1 (节点中心点) */
  x: number;
  y: number;
  /** 类型, 控制颜色 / 字号 / 光晕 */
  kind?: NodeKind;
};

type ConceptEdge = {
  from: string;
  to: string;
  label?: string;
};

type Keyframe = {
  /** 节点 ID 或边 ID (`from->to`) */
  id: string;
  atSec: number;
};

export interface DynamicConceptMapProps {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
  keyframes: Keyframe[];
  palette?: Palette;
  fadeInDurationMs?: number;
}

// 把 #RRGGBB 颜色按比例混入另一个 #RRGGBB. ratio=0 → b, ratio=1 → a
const mixHex = (a: string, b: string, ratio: number): string => {
  const ah = a.replace("#", "");
  const bh = b.replace("#", "");
  const ar = parseInt(ah.slice(0, 2), 16);
  const ag = parseInt(ah.slice(2, 4), 16);
  const ab = parseInt(ah.slice(4, 6), 16);
  const br = parseInt(bh.slice(0, 2), 16);
  const bg = parseInt(bh.slice(2, 4), 16);
  const bb = parseInt(bh.slice(4, 6), 16);
  const r = Math.round(br + (ar - br) * ratio);
  const g = Math.round(bg + (ag - bg) * ratio);
  const bch = Math.round(bb + (ab - bb) * ratio);
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${bch.toString(16).padStart(2, "0")}`;
};

// 树岛坂风格 (2026-06-01 真去看 BV18RoNBgELq 4m30s 后校准):
// 字号接近均匀, 不要大梯度. root/main/leaf 高度近似, 视觉重量靠"位置+描边" 不靠"大小".
const NODE_KIND_SCALE: Record<NodeKind, number> = {
  root: 1.0,
  main: 0.92,
  leaf: 0.85,
};

const NODE_KIND_FONT: Record<NodeKind, number> = {
  root: 0.044,  // 跟 main 接近, 不再夸张
  main: 0.038,
  leaf: 0.034,
};

export const DynamicConceptMap: React.FC<DynamicConceptMapProps> = ({
  nodes,
  edges,
  keyframes,
  palette = PALETTES.editorial_dark,
  fadeInDurationMs = MOTION_DURATION.base,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // 每个 ID 的"出现 progress 0→1" (spring 物理, 弹一下)
  const progressOf = (id: string): number => {
    const kf = keyframes.find((k) => k.id === id);
    if (!kf) return 1;
    const startFrame = kf.atSec * fps;
    return spring({
      frame: frame - startFrame,
      fps,
      config: { damping: 12, stiffness: 140, mass: 0.7 },
      durationInFrames: Math.round(fadeInDurationMs / 1000 * fps * 1.3),
    });
  };

  // 节点是否"刚刚出现" (用作 ring 强调, 1.5s 内)
  const recencyOf = (id: string): number => {
    const kf = keyframes.find((k) => k.id === id);
    if (!kf) return 0;
    const startFrame = kf.atSec * fps;
    const ringDurFrames = 1.5 * fps;
    return interpolate(frame, [startFrame, startFrame + ringDurFrames], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: (t) => 1 - Math.pow(1 - t, 3),
    });
  };

  // 估算节点宽度 (按文字长度自适应, 让短 label 不撑出大框, 长 label 也不挤)
  const estimateLabelWidth = (label: string, fontSize: number): number => {
    let charW = 0;
    for (const c of label) {
      if (/[一-龥]/.test(c)) charW += 1.0;        // 中文方块字
      else if (/[a-zA-Z0-9]/.test(c)) charW += 0.6; // 英数
      else charW += 0.5;                            // 符号 / 空格
    }
    return Math.round(charW * fontSize);
  };

  // 节点尺寸 (按 kind + label 长度自适应, 树岛坂 4m30s 实测节点占屏宽 1/6 左右)
  const sizeForKind = (kind: NodeKind, label: string = "") => {
    const baseH = height * 0.11;
    const s = NODE_KIND_SCALE[kind];
    const fontSize = Math.round(height * NODE_KIND_FONT[kind]);
    const labelW = estimateLabelWidth(label, fontSize);
    const padX = Math.round(fontSize * 1.2); // 左右各 1.2 字号留白 (跟树岛坂松弛感对齐)
    const minW = fontSize * 4;               // 至少 4 字号 (短 label 兜底, 避免太窄)
    const w = Math.max(minW, labelW + padX * 2);
    return {
      w: Math.round(w),
      h: Math.round(baseH * s),
      fontSize,
    };
  };

  const edgeFontSize = Math.round(height * TYPE_RATIO.body);

  // 节点中心点
  const nodeCenters = new Map<string, { cx: number; cy: number; kind: NodeKind }>();
  for (const n of nodes) {
    nodeCenters.set(n.id, {
      cx: n.x * width,
      cy: n.y * height,
      kind: n.kind ?? "main",
    });
  }

  return (
    <AbsoluteFill style={{ background: palette.bg }}>

      {/* SVG 层: 边 */}
      <svg
        style={{ position: "absolute", left: 0, top: 0, width: "100%", height: "100%" }}
        width={width}
        height={height}
      >
        <defs>
          <marker
            id="arrowhead"
            viewBox="0 0 12 12"
            refX="10"
            refY="6"
            markerWidth="10"
            markerHeight="10"
            orient="auto"
          >
            <path d="M 0 0 L 12 6 L 0 12 L 3 6 z" fill={palette.text} />
          </marker>
        </defs>
        {edges.map((e) => {
          const edgeId = `${e.from}->${e.to}`;
          const progress = progressOf(edgeId);
          const a = nodeCenters.get(e.from);
          const b = nodeCenters.get(e.to);
          if (!a || !b) return null;

          const aSize = sizeForKind(a.kind);
          const bSize = sizeForKind(b.kind);

          // 算线段方向, 从节点边界 (按矩形 half-extent + buffer) 退出
          const dx = b.cx - a.cx;
          const dy = b.cy - a.cy;
          const len = Math.hypot(dx, dy) || 1;
          const ux = dx / len;
          const uy = dy / len;
          const aRetract = Math.min(aSize.w / 2, aSize.h / 2) + 10;
          const bRetract = Math.min(bSize.w / 2, bSize.h / 2) + 14;
          const x1 = a.cx + ux * aRetract;
          const y1 = a.cy + uy * aRetract;
          const x2 = b.cx - ux * bRetract;
          const y2 = b.cy - uy * bRetract;

          const pathLen = Math.hypot(x2 - x1, y2 - y1);
          const drawn = pathLen * progress;
          const labelMidX = (x1 + x2) / 2;
          const labelMidY = (y1 + y2) / 2;

          return (
            <g key={edgeId}>
              {/* 树岛坂风格: 细虚线, 不要粗实线 + 大箭头 */}
              <line
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={palette.textSecondary}
                strokeWidth={1.5}
                strokeLinecap="round"
                strokeDasharray={`${Math.min(drawn, 5)} 5 ${Math.max(0, drawn - 5)} ${pathLen}`}
                opacity={Math.min(1, progress * 1.5)}
              />
              {e.label && progress > 0.55 && (
                <g opacity={(progress - 0.55) * 2.2}>
                  {/* 椭圆 pill 微透明背景, 不抢戏 */}
                  <rect
                    x={labelMidX - e.label.length * edgeFontSize * 0.45}
                    y={labelMidY - edgeFontSize * 0.85}
                    width={e.label.length * edgeFontSize * 0.9}
                    height={edgeFontSize * 1.7}
                    rx={edgeFontSize * 0.85}
                    fill={palette.bg}
                    opacity={0.85}
                  />
                  <text
                    x={labelMidX}
                    y={labelMidY}
                    fill={palette.accent}
                    fontFamily={FONT_STACK.body}
                    fontSize={edgeFontSize}
                    fontWeight={FONT_WEIGHT[6]}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    letterSpacing="0.1em"
                  >
                    {e.label}
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>

      {/* DIV 层: 节点 */}
      {nodes.map((n) => {
        const kind = n.kind ?? "main";
        const center = nodeCenters.get(n.id)!;
        const progress = progressOf(n.id);
        const recency = recencyOf(n.id);
        const { w, h, fontSize } = sizeForKind(kind);
        const scale = progress;

        // 树岛坂风格: 全黑底 + 1px 灰描边, 不要填色 + 光晕.
        // accent 只留给"反讽结论"类突出节点 (用 prop.emphasize 控制, 但 v4 全 false).
        const bg = palette.bg;
        const textColor = palette.text;
        const border = `1px solid ${palette.textSecondary}88`;
        const baseShadow = "none";
        const ringShadow =
          recency > 0
            ? `, 0 0 0 ${Math.round(recency * 6)}px ${palette.accent}${Math.round(recency * 0x60).toString(16).padStart(2, "0")}`
            : "";

        return (
          <div
            key={n.id}
            style={{
              position: "absolute",
              left: center.cx - w / 2,
              top: center.cy - h / 2,
              width: w,
              height: h,
              opacity: Math.min(1, progress * 1.2),
              transform: `scale(${scale})`,
              transformOrigin: "center",
              background: bg,
              color: textColor,
              border,
              borderRadius: kind === "root" ? 18 : 12,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: FONT_STACK.display,
              fontSize,
              fontWeight: kind === "leaf" ? FONT_WEIGHT[5] : FONT_WEIGHT[7],
              lineHeight: LINE_HEIGHT[1],
              letterSpacing: LETTER_SPACING[2],
              boxShadow: baseShadow + ringShadow,
              textAlign: "center",
              padding: `0 ${SIZE[3]}px`,
              whiteSpace: "nowrap",  // 不折行, 让宽度真自适应 (避免 "时间+金钱" 被压成 3 行)
              overflow: "visible",
            }}
          >
            {n.label}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
