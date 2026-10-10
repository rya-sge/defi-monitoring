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
import { KIND_COLOR, NAME_SLOT, nodeDrawing, tokenIconUrl } from '../lib/graph';

export type RiskNodeData = { node: GraphNode; amount: string[] };
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
const NODE_FILL = 'color-mix(in srgb, var(--fg) 5%, var(--bg))';
/** Selected: a 2px border in the kind colour and a 6px halo of it at 10 % opacity. */
const HALO = 6;
const halo = (colour: string) => `color-mix(in srgb, ${colour} 10%, transparent)`;

export function RiskNode({ data, selected }: NodeProps<RiskNodeType>) {
  const { node, amount } = data;
  const { shape, width, height, icon } = nodeDrawing(node);
  const colour = KIND_COLOR[node.kind];
  const iconSize = Math.round(Math.min(width, height) * 0.48);
  const logo = tokenIconUrl(node);
  const [logoFailed, setLogoFailed] = useState(false);
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
          {selected ? (
            <polygon
              points={HEXAGON}
              strokeLinejoin="round"
              style={{ fill: 'none', stroke: halo(colour) }}
              strokeWidth={HALO * 2}
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
          <polygon
            points={HEXAGON}
            strokeLinejoin="round"
            style={{ fill: NODE_FILL, stroke: selected ? colour : 'none' }}
            strokeWidth={2}
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      ) : (
        <div
          className="absolute inset-0"
          style={{
            background: NODE_FILL,
            border: selected ? `2px solid ${colour}` : undefined,
            boxShadow: selected ? `0 0 0 ${HALO}px ${halo(colour)}` : undefined,
            borderRadius: shape === 'circle' ? '50%' : shape === 'rounded' ? 20 : 6,
          }}
        />
      )}

      {/* Centred in the node and sized to it; the amount, drawn after, sits over it. */}
      <div className="absolute inset-0 flex items-center justify-center">
        {logo && !logoFailed ? (
          <img
            src={logo}
            alt=""
            className="rounded-full"
            style={{ width: iconSize * 1.2, height: iconSize * 1.2 }}
            onError={() => setLogoFailed(true)}
          />
        ) : (
          createElement(icon, {
            style: { color: colour, width: iconSize, height: iconSize },
            'aria-hidden': true,
          })
        )}
      </div>

      {amount.length > 0 ? (
        <div className="absolute inset-x-0.5 bottom-1 flex flex-col items-center gap-px">
          {amount.map((line) => (
            <div key={line} className={`${AMOUNT} max-w-full truncate`}>
              {line}
            </div>
          ))}
        </div>
      ) : null}

      {/* Counter-scaled for legibility, but kept inside its layout slot: narrower as it grows,
          and one line once two would no longer fit the slot's height. */}
      <div
        className={`absolute top-full left-1/2 mt-1 origin-top bg-background/80 text-center text-[11px] leading-tight text-foreground ${
          scale > 1.4 ? 'line-clamp-1' : 'line-clamp-2'
        }`}
        style={{
          width: NAME_SLOT.width / scale,
          transform: `translateX(-50%) scale(${scale})`,
        }}
        title={node.label}
      >
        {node.label}
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
          strokeWidth: data?.width ?? 1,
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
            {data.label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}
