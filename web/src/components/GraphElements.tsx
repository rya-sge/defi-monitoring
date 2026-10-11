import { FormattedText } from './FormattedText';
import { createElement, useState } from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  Handle,
  Position,
  getBezierPath,
  useStore,
} from '@xyflow/react';
import type { Edge, EdgeProps, Node, NodeProps } from '@xyflow/react';
import type { GraphEdge, GraphNode } from '../api/types';
import { GROUP_KEY, KIND_COLOR, NAME_SLOT, nodeDrawing, nodeRole, logoUrl } from '../lib/graph';

/** `ring`: a colour to ring the node with when it is not selected (the impact page's status). */
export type RiskNodeData = {
  node: GraphNode;
  amount: string[];
  ring?: string;
  underlying?: GraphNode;
  /** A pool's assets, collateral first (two or more replace its icon); a vault's asset. */
  assets?: GraphNode[];
};
export type RiskEdgeData = { edge: GraphEdge; label: string; width: number; colour: string };
export type RiskNodeType = Node<RiskNodeData, 'risk'>;
export type RiskEdgeType = Edge<RiskEdgeData, 'risk'>;

/**
 * Names and edge labels keep their set size when zooming out and are not magnified when
 * zooming in (D65); the amount inside a node scales with it, or it would overflow.
 */
function useLabelScale(): number {
  const zoom = useStore((s) => s.transform[2]);
  return Math.min(2.5, Math.max(1, 1 / zoom));
}

const HEXAGON = '15,1 45,1 59,26 45,51 15,51 1,26';
const HIDDEN_HANDLE = '!pointer-events-none !opacity-0';

/** Every amount, in a node or on an edge, is set the same way: one face, one size, one box. */
const AMOUNT =
  'rounded-sm bg-[color-mix(in_srgb,var(--fg)_8%,var(--bg))] px-1 text-[9px] leading-[1.4] text-foreground tabular-nums';

/** Every node sits on the same neutral ground; the kind colour is carried by the icon alone. */
const NODE_FILL = 'color-mix(in srgb, var(--fg) 12%, var(--bg))';
/** Selected: a 2px border in the kind colour and a 6px halo of it at 10 % opacity. */
const HALO = 6;
const halo = (colour: string) => `color-mix(in srgb, ${colour} 10%, transparent)`;

/** A token's or an oracle provider's logo, or the node kind's glyph if the logo does not load. */
function Logo({
  token,
  size,
  colour,
  url = logoUrl(token),
}: {
  token: GraphNode;
  size: number;
  colour: string;
  url?: string | null;
}) {
  const [failed, setFailed] = useState(false);
  return url && !failed ? (
    <img
      src={url}
      alt=""
      className="shrink-0 rounded-full"
      style={{
        width: size,
        height: size,
        background: NODE_FILL,
        boxShadow: `0 0 0 2px ${NODE_FILL}`,
      }}
      onError={() => setFailed(true)}
    />
  ) : (
    createElement(nodeDrawing(token).icon, {
      className: 'shrink-0',
      style: { color: colour, width: size * 0.8, height: size * 0.8 },
      'aria-hidden': true,
    })
  );
}

export function RiskNode({ data, selected }: NodeProps<RiskNodeType>) {
  const { node, amount } = data;
  const ring = selected ? KIND_COLOR[node.kind] : data.ring;
  const { shape, width, height, icon } = nodeDrawing(node);
  const colour = KIND_COLOR[node.kind];
  const iconSize = Math.round(Math.min(width, height) * 0.48);
  const curator = node.details.curator_image;
  // A PT carries its underlying's logo; a vault, its curator's.
  const badge =
    node.kind === 'Asset' && node.label.toUpperCase().startsWith('PT-') && data.underlying
      ? { token: data.underlying, url: logoUrl(data.underlying), title: data.underlying.label }
      : typeof curator === 'string'
        ? { token: node, url: curator, title: String(node.details.curator) }
        : undefined;
  const pair = data.assets && data.assets.length >= 2 ? data.assets : undefined;
  const logo =
    node.kind === 'Asset' || node.kind === 'Oracle'
      ? node
      : nodeRole(node) === 'vault'
        ? data.assets?.[0]
        : undefined;
  const scale = useLabelScale();

  return (
    <div className="relative" style={{ width, height }}>
      {shape === 'hexagon' ? (
        // An SVG polygon, so the border follows the shape; a clip-path would cut it off.
        // The halo is a wide stroke under the shape: half of it shows outside the edge.
        <svg
          className="absolute inset-0 size-full overflow-visible"
          viewBox="0 0 60 52"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          {GROUP_KEY in node.details
            ? [8, 4].map((offset) => (
                <polygon
                  key={offset}
                  points={HEXAGON}
                  transform={`translate(${offset} ${-offset})`}
                  style={{
                    fill: `color-mix(in srgb, var(--fg) ${offset === 8 ? 5 : 8}%, var(--bg))`,
                    stroke: 'var(--bg)',
                  }}
                  strokeWidth={1}
                  vectorEffect="non-scaling-stroke"
                />
              ))
            : null}
          {ring ? (
            <polygon
              points={HEXAGON}
              strokeLinejoin="round"
              style={{ fill: 'none', stroke: halo(ring) }}
              strokeWidth={HALO * 2}
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
          <polygon
            points={HEXAGON}
            strokeLinejoin="round"
            style={{ fill: NODE_FILL, stroke: ring ?? 'none' }}
            strokeWidth={2}
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      ) : (
        <>
          {GROUP_KEY in node.details
            ? [8, 4].map((offset) => (
                // Two cards behind a group of twins: it stands for several nodes.
                <div
                  key={offset}
                  className="absolute inset-0 rounded-md"
                  style={{
                    transform: `translate(${offset}px, ${-offset}px)`,
                    background: `color-mix(in srgb, var(--fg) ${offset === 8 ? 5 : 8}%, var(--bg))`,
                    boxShadow: '-1px 1px 0 var(--bg)',
                  }}
                />
              ))
            : null}
          <div
            className="absolute inset-0"
            style={{
              // A vault is tinted with its kind colour: it is what the graph is about.
              background:
                nodeRole(node) === 'vault'
                  ? `color-mix(in srgb, ${colour} 22%, var(--bg))`
                  : NODE_FILL,
              border: ring ? `2px solid ${ring}` : undefined,
              boxShadow: ring ? `0 0 0 ${HALO}px ${halo(ring)}` : undefined,
              borderRadius: shape === 'circle' ? '50%' : shape === 'rounded' ? 20 : 6,
            }}
          />
        </>
      )}

      {/* Centred in the node and sized to it; the amount, drawn after, sits over it. */}
      <div className="absolute inset-0 flex items-center justify-center">
        {pair ? (
          <div className="flex items-center" title={pair.map((a) => a.label).join(' / ')}>
            {pair.map((asset, i) => (
              <div key={asset.id} style={{ marginLeft: i ? -iconSize * 0.35 : 0 }}>
                <Logo token={asset} size={iconSize} colour={colour} />
              </div>
            ))}
          </div>
        ) : (
          <div className="relative">
            {logo ? (
              <Logo token={logo} size={iconSize * 1.2} colour={colour} />
            ) : (
              createElement(icon, {
                style: { color: colour, width: iconSize, height: iconSize },
                'aria-hidden': true,
              })
            )}
            {badge ? (
              <div
                className="absolute -top-1 -right-2 flex size-4 items-center justify-center"
                title={badge.title}
              >
                <Logo token={badge.token} url={badge.url} size={16} colour={colour} />
              </div>
            ) : null}
          </div>
        )}
      </div>

      {amount.length > 0 ? (
        <div className="absolute inset-x-0.5 bottom-1 flex flex-col items-center gap-px">
          {amount.map((line) => (
            <div key={line} className={`${AMOUNT} max-w-full truncate`}>
              <FormattedText>{line}</FormattedText>
            </div>
          ))}
        </div>
      ) : null}

      {/* Counter-scaled for legibility, but kept inside its layout slot: narrower as it grows,
          and one line once two would no longer fit the slot's height. */}
      <div
        className={`absolute top-full left-1/2 mt-1 origin-top rounded-md bg-[var(--surface)] px-1 py-0.5 text-center text-[11px] leading-tight text-foreground ${
          scale > 1.4 ? 'line-clamp-1' : 'line-clamp-2'
        }`}
        style={{
          width: NAME_SLOT.width / scale,
          transform: `translateX(-50%) scale(${scale})`,
        }}
        title={node.label}
      >
        <FormattedText>{node.label}</FormattedText>
      </div>

      <Handle
        type="target"
        position={Position.Top}
        isConnectable={false}
        className={HIDDEN_HANDLE}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        isConnectable={false}
        className={HIDDEN_HANDLE}
      />
    </div>
  );
}

export function RiskEdge({
  id,
  data,
  selected,
  markerEnd,
  style,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
}: EdgeProps<RiskEdgeType>) {
  const [path, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });
  const scale = useLabelScale();

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: selected ? 'var(--fg)' : (data?.colour ?? 'var(--edge)'),
          strokeWidth: Math.max(2, data?.width ?? 2),
          // No amount: a dependency, not a flow of funds.
          strokeDasharray: data?.edge.amount == null ? '4 3' : undefined,
        }}
      />
      {data?.label ? (
        <EdgeLabelRenderer>
          <div
            className={`${AMOUNT} pointer-events-none absolute`}
            style={{
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px) scale(${scale})`,
              opacity: style?.opacity,
            }}
          >
            <FormattedText>{data.label}</FormattedText>
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}
